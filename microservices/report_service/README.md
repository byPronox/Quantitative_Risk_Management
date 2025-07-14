# Report Generation Service

Microservice for generating comprehensive vulnerability assessment reports from MongoDB data.

## Features

- **Multiple Report Types:**
  - Vulnerability Summary Reports
  - Risk Assessment Reports
  - Compliance Reports
  - Executive Summary Reports

- **Multiple Formats:**
  - PDF (for printing and archival)
  - HTML (interactive web viewing)

- **Data Sources:**
  - MongoDB Atlas integration
  - NVD Service data consumption
  - Vulnerability session filtering

- **Report Features:**
  - Executive summaries
  - Risk metrics and distributions
  - Critical vulnerability highlights
  - Automated recommendations
  - Charts and visualizations

## API Endpoints

- `POST /api/reports/generate` - Generate new report
- `GET /api/reports/{report_id}/download` - Download report file
- `GET /api/reports/{report_id}/preview` - Preview HTML report
- `GET /api/reports/{report_id}/info` - Get report information
- `GET /api/reports/types` - Get available report types and formats
- `DELETE /api/reports/{report_id}` - Delete generated report

## Environment Variables

- `MONGODB_URL` - MongoDB connection string
- `MONGODB_DATABASE` - Database name
- `BACKEND_SERVICE_URL` - Backend service URL
- `NVD_SERVICE_URL` - NVD service URL
- `REPORTS_TEMP_DIR` - Temporary directory for generated reports

## Docker

The service runs on port 8003 and connects to MongoDB Atlas for vulnerability data.

## Usage

1. Generate reports through the frontend or API
2. Download PDF reports for offline use
3. Preview HTML reports in browser
4. Reports automatically include vulnerability metrics and recommendations
