-- Database initialization script for AI Procurement & Vendor Intelligence Platform

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create dedicated schema for LangGraph persistent checkpoints
CREATE SCHEMA IF NOT EXISTS checkpoints;

-- Grant permissions on checkpoints schema
GRANT ALL ON SCHEMA checkpoints TO procure_user;
