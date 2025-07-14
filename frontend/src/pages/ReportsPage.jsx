import React from 'react';
import GeneralReports from '../components/GeneralReports';

const ReportsPage = () => {
  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', color: '#2c3e50', marginBottom: '30px' }}>
        Reports Dashboard
      </h1>

      {/* General Reports Content */}
      <GeneralReports />
    </div>
  );
};

export default ReportsPage;
