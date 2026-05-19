#!/bin/bash

# QURVE AI - Production Startup Script
# This script orchestrates the startup of all production services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required files exist
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if [ ! -f "docker-compose.prod.yml" ]; then
        log_error "docker-compose.prod.yml not found"
        exit 1
    fi
    
    if [ ! -f ".env.prod" ]; then
        log_error ".env.prod file not found"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Load environment variables
load_environment() {
    log_info "Loading production environment variables..."
    export $(cat .env.prod | grep -v '^#' | xargs)
    log_success "Environment variables loaded"
}

# Validate environment configuration
validate_environment() {
    log_info "Validating environment configuration..."
    
    # Check required environment variables
    required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "GRAFANA_USER"
        "GRAFANA_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log_success "Environment validation passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p logs/nginx
    mkdir -p logs/backend
    mkdir -p logs/frontend
    mkdir -p backups
    mkdir -p config
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/prometheus
    mkdir -p data/grafana
    mkdir -p data/loki
    
    # Set proper permissions
    chmod 755 logs
    chmod 755 backups
    chmod 755 config
    chmod 755 data
    
    log_success "Directories created"
}

# Pull latest images
pull_images() {
    log_info "Pulling latest Docker images..."
    docker-compose -f docker-compose.prod.yml pull
    log_success "Images pulled"
}

# Start services in dependency order
start_services() {
    log_info "Starting QURVE AI production services..."
    
    # Start database and cache first
    log_info "Starting database and cache services..."
    docker-compose -f docker-compose.prod.yml up -d postgres redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 30
    
    # Check database health
    if ! docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U qubo_user -d qubo_platform; then
        log_error "Database is not ready"
        exit 1
    fi
    
    # Check Redis health
    if ! docker-compose -f docker-compose.prod.yml exec redis redis-cli ping; then
        log_error "Redis is not ready"
        exit 1
    fi
    
    log_success "Database and cache are ready"
    
    # Start backend services
    log_info "Starting backend services..."
    docker-compose -f docker-compose.prod.yml up -d qubo-backend
    
    # Wait for backend to be ready
    log_info "Waiting for backend to be ready..."
    sleep 60
    
    # Check backend health
    if ! curl -f http://localhost:8000/health; then
        log_error "Backend is not ready"
        exit 1
    fi
    
    log_success "Backend is ready"
    
    # Start frontend
    log_info "Starting frontend..."
    docker-compose -f docker-compose.prod.yml up -d qubo-frontend
    
    # Wait for frontend to be ready
    log_info "Waiting for frontend to be ready..."
    sleep 30
    
    # Check frontend health
    if ! curl -f http://localhost:3000/health; then
        log_error "Frontend is not ready"
        exit 1
    fi
    
    log_success "Frontend is ready"
    
    # Start monitoring services
    log_info "Starting monitoring services..."
    docker-compose -f docker-compose.prod.yml up -d prometheus grafana loki
    
    # Wait for monitoring services
    log_info "Waiting for monitoring services to be ready..."
    sleep 30
    
    log_success "Monitoring services started"
    
    # Start reverse proxy
    log_info "Starting reverse proxy..."
    docker-compose -f docker-compose.prod.yml up -d nginx
    
    # Wait for nginx to be ready
    log_info "Waiting for reverse proxy to be ready..."
    sleep 15
    
    # Check nginx health
    if ! curl -f http://localhost/health; then
        log_error "Reverse proxy is not ready"
        exit 1
    fi
    
    log_success "Reverse proxy is ready"
    
    # Start backup service
    log_info "Starting backup service..."
    docker-compose -f docker-compose.prod.yml up -d backup
    
    log_success "All services started successfully"
}

# Verify service health
verify_health() {
    log_info "Verifying service health..."
    
    services=(
        "postgres"
        "redis"
        "qubo-backend"
        "qubo-frontend"
        "prometheus"
        "grafana"
        "loki"
        "nginx"
        "backup"
    )
    
    unhealthy_services=()
    
    for service in "${services[@]}"; do
        health=$(docker-compose -f docker-compose.prod.yml ps -q $service | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        
        if [ "$health" = "healthy" ]; then
            log_success "$service is healthy"
        else
            log_warning "$service health status: $health"
            unhealthy_services+=($service)
        fi
    done
    
    if [ ${#unhealthy_services[@]} -gt 0 ]; then
        log_warning "Some services are not healthy: ${unhealthy_services[*]}"
        log_info "Waiting 60 seconds for services to become healthy..."
        sleep 60
        
        # Re-check
        for service in "${unhealthy_services[@]}"; do
            health=$(docker-compose -f docker-compose.prod.yml ps -q $service | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
            
            if [ "$health" = "healthy" ]; then
                log_success "$service is now healthy"
            else
                log_error "$service is still not healthy"
            fi
        done
    fi
}

# Display startup summary
display_summary() {
    log_info "QURVE AI Production Startup Summary"
    echo "=================================="
    echo "Frontend: http://localhost"
    echo "Backend API: http://localhost/api"
    echo "Grafana Dashboard: http://localhost:3001"
    echo "Prometheus: http://localhost:9090"
    echo "=================================="
    echo ""
    echo "Service Status:"
    docker-compose -f docker-compose.prod.yml ps
    echo ""
    echo "Logs can be viewed with:"
    echo "  docker-compose -f docker-compose.prod.yml logs -f [service-name]"
    echo ""
    echo "To stop all services:"
    echo "  docker-compose -f docker-compose.prod.yml down"
    echo ""
    log_success "QURVE AI production startup completed successfully!"
}

# Main execution
main() {
    log_info "Starting QURVE AI production deployment..."
    echo ""
    
    check_prerequisites
    load_environment
    validate_environment
    create_directories
    pull_images
    start_services
    verify_health
    display_summary
}

# Handle script interruption
trap 'log_warning "Startup interrupted"; exit 1' INT TERM

# Run main function
main "$@"
