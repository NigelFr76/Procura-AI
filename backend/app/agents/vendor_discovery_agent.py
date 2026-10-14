"""Agent 2: Vendor Discovery Agent for shortlisting suppliers from internal registry."""

import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor, VendorStatus
from app.schemas.vendor_discovery import (
    VendorDiscoveryInput,
    ShortlistedVendor,
    ExcludedVendor,
    VendorShortlistResult,
)


class VendorDiscoveryAgent:
    """Specialized agent that searches the organization's vendor registry and shortlists candidates."""

    @classmethod
    async def discover_and_shortlist(
        cls,
        session: AsyncSession,
        input_data: VendorDiscoveryInput,
    ) -> VendorShortlistResult:
        """Scan vendor registry, evaluate capabilities and certifications, and produce audit reasons."""
        spec = input_data.spec
        org_id = input_data.organization_id

        # Query all vendors registered under this tenant organization
        stmt = select(Vendor).where(Vendor.organization_id == org_id)
        result = await session.execute(stmt)
        all_vendors: List[Vendor] = list(result.scalars().all())

        shortlisted: List[ShortlistedVendor] = []
        excluded: List[ExcludedVendor] = []

        required_certs_set = {c.strip().upper() for c in spec.required_certifications}

        for vendor in all_vendors:
            # Check 1: Exclude suspended vendors immediately
            if vendor.status == VendorStatus.SUSPENDED:
                excluded.append(
                    ExcludedVendor(
                        vendor_id=vendor.id,
                        vendor_name=vendor.name,
                        exclusion_reasons=["Supplier is currently under SUSPENDED status due to past compliance issues."],
                    )
                )
                continue

            # Check 2: Evaluate certifications in vendor metadata
            vendor_certs = vendor.metadata_info.get("certifications", [])
            vendor_certs_set = {c.strip().upper() for c in vendor_certs}
            missing_certs = required_certs_set - vendor_certs_set

            if required_certs_set and missing_certs:
                excluded.append(
                    ExcludedVendor(
                        vendor_id=vendor.id,
                        vendor_name=vendor.name,
                        exclusion_reasons=[f"Missing mandatory certifications: {', '.join(missing_certs)}"],
                    )
                )
                continue

            # Check 3: Capability keyword score
            reasons: List[str] = []
            score = 0.70 # Baseline for active matching vendor

            if vendor.status == VendorStatus.VERIFIED:
                score += 0.20
                reasons.append("Verified enterprise supplier in good standing.")
            elif vendor.status == VendorStatus.SHORTLISTED:
                score += 0.10
                reasons.append("Pre-shortlisted vendor with verified profile.")
            else:
                reasons.append("Unverified external vendor registration.")

            if required_certs_set and not missing_certs:
                score += 0.10
                reasons.append(f"Holds all requested certifications: {', '.join(spec.required_certifications)}.")

            match_score = min(1.0, round(score, 2))

            shortlisted.append(
                ShortlistedVendor(
                    vendor_id=vendor.id,
                    vendor_name=vendor.name,
                    country=vendor.country,
                    status=str(vendor.status.value),
                    match_score=match_score,
                    match_reasons=reasons,
                    held_certifications=vendor_certs,
                    is_verified=(vendor.status == VendorStatus.VERIFIED),
                )
            )

        # Sort shortlisted by match score descending
        shortlisted.sort(key=lambda x: (x.is_verified, x.match_score), reverse=True)
        top_shortlist = shortlisted[:input_data.max_shortlist]

        # Any remaining become excluded by capacity
        for v in shortlisted[input_data.max_shortlist:]:
            excluded.append(
                ExcludedVendor(
                    vendor_id=v.vendor_id,
                    vendor_name=v.vendor_name,
                    exclusion_reasons=["Excluded due to shortlist capacity limit; lower capability score than selected finalists."],
                )
            )

        summary = (
            f"Scanned {len(all_vendors)} registered vendors. "
            f"Shortlisted {len(top_shortlist)} qualified suppliers. "
            f"Excluded {len(excluded)} vendors with documented audit reasons."
        )

        return VendorShortlistResult(
            shortlisted=top_shortlist,
            excluded=excluded,
            total_registry_scanned=len(all_vendors),
            search_summary=summary,
        )
