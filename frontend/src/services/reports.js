import api from './api.js';

export const reportService = {
  async generateReport(reportRequest) {
    try {
      const response = await api.post('/report-service/api/reports/generate', reportRequest);
      return response.data;
    } catch (error) {
      console.error('Error generating report:', error);
      throw error;
    }
  },

  async getReportInfo(reportId) {
    try {
      const response = await api.get(`/report-service/api/reports/${reportId}/info`);
      return response.data;
    } catch (error) {
      console.error('Error getting report info:', error);
      throw error;
    }
  },

  async downloadReport(reportId) {
    try {
      const response = await api.get(`/report-service/api/reports/${reportId}/download`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'reporte_vulnerabilidades.pdf';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('Error downloading report:', error);
      throw error;
    }
  },

  getPreviewUrl(reportId) {
    return `/api/report-service/api/reports/${reportId}/preview`;
  },

  async getReportTypes() {
    try {
      const response = await api.get('/report-service/api/reports/types');
      return response.data;
    } catch (error) {
      console.error('Error getting report types:', error);
      throw error;
    }
  },

  async deleteReport(reportId) {
    try {
      const response = await api.delete(`/report-service/api/reports/${reportId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting report:', error);
      throw error;
    }
  }
};
