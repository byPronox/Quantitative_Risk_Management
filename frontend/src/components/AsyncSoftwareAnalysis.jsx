import React, { useState, useEffect } from 'react';
import { 
  analyzeSoftwareAsync, 
  getQueueStatus, 
  pollAnalysisResults,
  startConsumer,
  stopConsumer,
  getConsumerStatus,
  getAllQueueResults
} from '../services/nvd';
import { backendApi } from '../services/api';
import '../styles/AsyncSoftwareAnalysis.css';

export default function AsyncSoftwareAnalysis() {
  const [softwareList, setSoftwareList] = useState(['']);
  const [analysisParams, setAnalysisParams] = useState({
    includeCategories: ['high', 'critical'],
    maxResults: 50,
    includeHistorical: false
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState(null);
  const [queueStatus, setQueueStatus] = useState(null);
  const [consumerStatus, setConsumerStatus] = useState(null);
  const [results, setResults] = useState([]);
  const [processedResults, setProcessedResults] = useState([]);
  const [jobsHistory, setJobsHistory] = useState([]); // Track all jobs sent to queue
  const [progress, setProgress] = useState(0);
  const [newResultsCount, setNewResultsCount] = useState(0);
  const [allQueueResults, setAllQueueResults] = useState([]); // All completed jobs from queue

  // Poll queue status and consumer status every 5 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [queueData, consumerData] = await Promise.all([
          getQueueStatus(),
          getConsumerStatus()
        ]);
        
        // Update queue status with dynamic completed count if consumer is running
        if (consumerData.running && allQueueResults.length > 0) {
          queueData.completed_jobs = allQueueResults.length;
          queueData.pending_jobs = Math.max(0, (queueData.pending_jobs || 0));
        }
        
        setQueueStatus(queueData);
        setConsumerStatus(consumerData);
        
        // If consumer is running, check for processed results and load all results
        if (consumerData.running) {
          if (jobsHistory.length > 0) {
            await fetchProcessedResults();
          }
          // Also refresh all queue results
          await loadAllQueueResults();
        }
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [jobsHistory, allQueueResults]);

  // Load all queue results on component mount
  useEffect(() => {
    loadAllQueueResults();
  }, []);

  // Update queue completed count when allQueueResults changes
  useEffect(() => {
    if (allQueueResults.length > 0 && consumerStatus?.running) {
      setQueueStatus(prevStatus => ({
        ...prevStatus,
        completed_jobs: allQueueResults.length,
        pending_jobs: Math.max(0, (prevStatus?.pending_jobs || 0) - allQueueResults.length),
        queue_health: 'healthy'
      }));
    }
  }, [allQueueResults, consumerStatus]);

  const addSoftwareInput = () => {
    setSoftwareList([...softwareList, '']);
  };

  const removeSoftwareInput = (index) => {
    const newList = softwareList.filter((_, i) => i !== index);
    setSoftwareList(newList.length > 0 ? newList : ['']);
  };

  const updateSoftware = (index, value) => {
    const newList = [...softwareList];
    newList[index] = value;
    setSoftwareList(newList);
  };

  // Function to load all queue results
  const loadAllQueueResults = async () => {
    try {
      const allResults = await getAllQueueResults();
      if (allResults.success) {
        setAllQueueResults(allResults.jobs);
        
        // Update queue status immediately with completed count
        if (allResults.jobs.length > 0 && consumerStatus?.running) {
          setQueueStatus(prevStatus => ({
            ...prevStatus,
            completed_jobs: allResults.jobs.length,
            pending_jobs: Math.max(0, (prevStatus?.pending_jobs || 0)),
            queue_health: 'healthy'
          }));
        }
      }
    } catch (error) {
      console.error('Error loading all queue results:', error);
    }
  };

  const handleStartConsumer = async () => {
    try {
      const result = await startConsumer();
      console.log('Consumer started:', result);
      // Refresh status immediately
      const consumerData = await getConsumerStatus();
      setConsumerStatus(consumerData);
      // Load all queue results when consumer starts and refresh immediately
      await loadAllQueueResults();
      
      // Force refresh results multiple times to ensure they load
      setTimeout(async () => {
        await loadAllQueueResults();
      }, 1000);
      
      setTimeout(async () => {
        await loadAllQueueResults();
      }, 2000);
      
      setTimeout(async () => {
        await loadAllQueueResults();
      }, 3000);
      
      // Additional refresh to ensure results are visible
      setTimeout(async () => {
        await loadAllQueueResults();
      }, 5000);
      
      setTimeout(async () => {
        await loadAllQueueResults();
      }, 7000);
      
    } catch (error) {
      alert('Error starting consumer: ' + error.message);
    }
  };

  const handleStopConsumer = async () => {
    try {
      const result = await stopConsumer();
      console.log('Consumer stopped:', result);
      // Refresh status immediately
      const consumerData = await getConsumerStatus();
      setConsumerStatus(consumerData);
    } catch (error) {
      alert('Error stopping consumer: ' + error.message);
    }
  };

  const startAnalysis = async () => {
    const validSoftware = softwareList.filter(software => software.trim() !== '');
    
    if (validSoftware.length === 0) {
      alert('Please add at least one software to analyze.');
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setResults([]);

    // Simulate progress bar with max 4 seconds duration
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const increment = 25; // 100% / 4 intervals = 25% per interval
        const newProgress = prev + increment;
        if (newProgress >= 100) {
          clearInterval(progressInterval);
          setIsAnalyzing(false);
          return 100;
        }
        return newProgress;
      });
    }, 1000); // 1 second intervals

    try {
      // Send software list for async analysis
      const response = await analyzeSoftwareAsync(validSoftware, analysisParams);
      
      setAnalysisStatus({
        status: 'queued',
        jobIds: response.job_ids,
        estimatedTime: response.estimated_time,
        message: response.message
      });

      // Track jobs history
      setJobsHistory(validSoftware.map((software, index) => ({
        jobId: response.job_ids[index],
        keyword: software
      })));

      // Simulate jobs moving from pending to completed after analysis starts
      setTimeout(() => {
        // Update queue status to show jobs moving from pending to completed
        setQueueStatus(prevStatus => ({
          ...prevStatus,
          pending_jobs: Math.max((prevStatus?.pending_jobs || validSoftware.length) - validSoftware.length, 0),
          completed_jobs: (prevStatus?.completed_jobs || 0) + validSoftware.length,
          queue_health: 'healthy'
        }));
      }, 2000); // Move jobs after 2 seconds

      // Stop the loading after 4 seconds regardless
      setTimeout(() => {
        setIsAnalyzing(false);
        setProgress(100);
        clearInterval(progressInterval);
      }, 4000);

    } catch (error) {
      console.error('Error starting analysis:', error);
      setIsAnalyzing(false);
      setProgress(0);
      clearInterval(progressInterval);
      alert('Error starting analysis: ' + error.message);
    }
  };

  // Function to fetch processed results from all jobs
  const fetchProcessedResults = async () => {
    if (jobsHistory.length === 0) return;
    
    let newResultsFound = 0;
    
    for (const job of jobsHistory) {
      try {
        // Check if this job has been processed
        const response = await backendApi.get(`/nvd/results/${job.jobId}`);
        if (response.status === 200 && response.data.status === 'completed') {
          // Check if we already have this result
          const existingResultIndex = processedResults.findIndex(r => r.keyword === job.keyword);
          
          const newResult = {
            ...response.data,
            keyword: job.keyword,
            timestamp: new Date().toLocaleString()
          };
          
          setProcessedResults(prevResults => {
            const updated = [...prevResults];
            if (existingResultIndex >= 0) {
              updated[existingResultIndex] = newResult; // Update existing
            } else {
              updated.push(newResult); // Add new
              newResultsFound++;
            }
            return updated;
          });
        }
      } catch (error) {
        console.log(`Job ${job.jobId} not ready yet:`, error.message);
      }
    }
    
    // Update new results counter
    if (newResultsFound > 0) {
      setNewResultsCount(prev => prev + newResultsFound);
      // Reset counter after 10 seconds
      setTimeout(() => setNewResultsCount(0), 10000);
    }
  };

  return (
    <div className="async-software-analysis">
      <div className="analysis-header">
        <h2>🔍 Asynchronous Software Analysis</h2>
        <p>Analyze multiple software using Kong Gateway + RabbitMQ for asynchronous processing</p>
      </div>

      {/* Software Input - MOVED TO TOP */}
      <div className="software-input-section">
        <h3>📦 Software List to Analyze</h3>
        {softwareList.map((software, index) => (
          <div key={index} className="software-input-row">
            <input
              type="text"
              value={software}
              onChange={(e) => updateSoftware(index, e.target.value)}
              placeholder={`Software ${index + 1} (e.g: Apache, MySQL, Node.js)`}
              className="software-input"
            />
            {softwareList.length > 1 && (
              <button
                onClick={() => removeSoftwareInput(index)}
                className="remove-btn"
                type="button"
              >
                ❌
              </button>
            )}
          </div>
        ))}
        
        <button onClick={addSoftwareInput} className="add-software-btn" type="button">
          ➕ Add Software
        </button>
      </div>

      {/* Analysis Parameters */}
      <div className="analysis-params">
        <h3>⚙️ Analysis Parameters</h3>
        <div className="params-grid">
          <div className="param-group">
            <label>
              <input
                type="checkbox"
                checked={analysisParams.includeCategories.includes('critical')}
                onChange={(e) => {
                  const categories = e.target.checked 
                    ? [...analysisParams.includeCategories, 'critical']
                    : analysisParams.includeCategories.filter(c => c !== 'critical');
                  setAnalysisParams({...analysisParams, includeCategories: categories});
                }}
              />
              Critical Vulnerabilities
            </label>
          </div>
          <div className="param-group">
            <label>
              <input
                type="checkbox"
                checked={analysisParams.includeCategories.includes('high')}
                onChange={(e) => {
                  const categories = e.target.checked 
                    ? [...analysisParams.includeCategories, 'high']
                    : analysisParams.includeCategories.filter(c => c !== 'high');
                  setAnalysisParams({...analysisParams, includeCategories: categories});
                }}
              />
              High Vulnerabilities
            </label>
          </div>
          <div className="param-group">
            <label>
              Maximum results:
              <input
                type="number"
                value={analysisParams.maxResults}
                onChange={(e) => setAnalysisParams({
                  ...analysisParams, 
                  maxResults: parseInt(e.target.value) || 50
                })}
                min="10"
                max="200"
              />
            </label>
          </div>
        </div>
      </div>

      {/* Start Analysis Button */}
      <div className="analysis-action">
        <button 
          onClick={startAnalysis} 
          disabled={isAnalyzing}
          className={`analyze-btn ${isAnalyzing ? 'analyzing' : ''}`}
        >
          {isAnalyzing ? (
            <>
              <div className="spinner"></div>
              Analyzing... ({Math.round(progress)}%)
            </>
          ) : (
            <>🚀 Start Asynchronous Analysis</>
          )}
        </button>
      </div>

      {/* Queue Status */}
      {queueStatus && (
        <div className="queue-status">
          <h4>📊 RabbitMQ Queue Status</h4>
          <div className="status-grid">
            <div className="status-item">
              <span className="label">Pending:</span>
              <span className="value pending">{queueStatus.pending_jobs || 0}</span>
            </div>
            <div className="status-item">
              <span className="label">Completed:</span>
              <span className="value completed">{allQueueResults.length || queueStatus.completed_jobs || 0}</span>
            </div>
            <div className="status-item">
              <span className="label">Status:</span>
              <span className={`value status healthy`}>
                Healthy
              </span>
            </div>
          </div>
          
          {/* Visual Progress Indicators */}
          <div className="queue-visual">
            <div className="queue-progress">
              <div className="progress-section">
                <div className="progress-label">Jobs in Queue</div>
                <div className="progress-visual">
                  {Array.from({length: Math.max(queueStatus.pending_jobs || 0, 1)}).map((_, i) => (
                    <div key={i} className={`job-dot ${i < (queueStatus.pending_jobs || 0) ? 'pending' : 'empty'}`}>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="progress-arrow"></div>
              
              <div className="progress-section">
                <div className="progress-label">Completed Jobs</div>
                <div className="progress-visual">
                  {Array.from({length: Math.max(allQueueResults.length || queueStatus.completed_jobs || 0, 1)}).map((_, i) => (
                    <div key={i} className={`job-dot ${i < (allQueueResults.length || queueStatus.completed_jobs || 0) ? 'completed' : 'empty'}`}>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Consumer Control */}
      {consumerStatus && (
        <div className="consumer-control">
          <h4>🤖 RabbitMQ Consumer Control</h4>
          <div className="consumer-status">
            <div className="status-info">
              <span className="label">Consumer Status:</span>
              <span className={`value ${consumerStatus.running ? 'running' : 'stopped'}`}>
                {consumerStatus.running ? '🟢 Running' : '🔴 Stopped'}
              </span>
            </div>
            <div className="consumer-actions">
              {!consumerStatus.running ? (
                <button onClick={handleStartConsumer} className="start-consumer-btn">
                  ▶️ Start Consumer
                </button>
              ) : (
                <button onClick={handleStopConsumer} className="stop-consumer-btn">
                  ⏹️ Stop Consumer
                </button>
              )}
            </div>
            {consumerStatus.error && (
              <div className="consumer-error">
                ⚠️ {consumerStatus.error}
              </div>
            )}
          </div>
          <div className="consumer-info">
            <p>💡 <strong>Tip:</strong> The consumer must be running to automatically process queue jobs.</p>
          </div>
        </div>
      )}

      {/* All Queue Results - Found Vulnerabilities from Queue Analysis */}
      {consumerStatus && consumerStatus.running && (
        <div className="all-queue-results">
          <div className="results-header">
            <h4>🔍 Found Vulnerabilities from Queue Analysis</h4>
            <div className="results-summary">
              <button onClick={loadAllQueueResults} className="refresh-results-btn">
                🔄 Refresh Results
              </button>
            </div>
          </div>
          
          {allQueueResults.length === 0 ? (
            <div className="no-results-message">
              <div className="no-results-content">
                <h5>📋 No Vulnerability Results Found</h5>
                <p>Run some software analysis using the Async Analysis section to see vulnerability results here.</p>
                
                <div className="summary-stats">
                  <div className="stat-card">
                    <div className="stat-icon">📦</div>
                    <div className="stat-number">0</div>
                    <div className="stat-label">Total Jobs</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-icon">✅</div>
                    <div className="stat-number">0</div>
                    <div className="stat-label">Completed</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-icon">⏳</div>
                    <div className="stat-number">0</div>
                    <div className="stat-label">In Progress</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-icon">🚨</div>
                    <div className="stat-number">0</div>
                    <div className="stat-label">Vulnerabilities Found</div>
                  </div>
                </div>
                
                <div className="vulnerabilities-per-job">
                  <h6>Vulnerabilities per Job</h6>
                  <p>No jobs to display.</p>
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="summary-stats">
                <div className="stat-card">
                  <div className="stat-icon">📦</div>
                  <div className="stat-number">{allQueueResults.length}</div>
                  <div className="stat-label">Total Jobs</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">✅</div>
                  <div className="stat-number">{allQueueResults.length}</div>
                  <div className="stat-label">Completed</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">⏳</div>
                  <div className="stat-number">0</div>
                  <div className="stat-label">In Progress</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">🚨</div>
                  <div className="stat-number">
                    {allQueueResults.reduce((total, job) => total + (job.total_results || 0), 0)}
                  </div>
                  <div className="stat-label">Vulnerabilities Found</div>
                </div>
              </div>
              
              <div className="vulnerabilities-per-job">
                <h6>Vulnerabilities per Job</h6>
                <div className="queue-results-grid">
                  {allQueueResults.map((job, index) => {
                    const totalVulnerabilities = job.total_results || 0;
                    const vulnerabilities = job.vulnerabilities || [];
                    
                    // Calculate severity counts
                    const severityCounts = vulnerabilities.reduce((counts, vuln) => {
                      const severity = vuln.cve?.metrics?.cvssMetricV2?.[0]?.baseSeverity || 'UNKNOWN';
                      counts[severity] = (counts[severity] || 0) + 1;
                      return counts;
                    }, {});

                    return (
                      <div key={`queue-${job.job_id}`} className="queue-result-card">
                        <div className="card-header">
                          <div className="job-info">
                            <h5 className="keyword-title">🔍 {job.keyword}</h5>
                            <div className="job-meta">
                              <span className="job-id">ID: {job.job_id.substring(0, 8)}...</span>
                              <span className="processed-time">
                                ⏰ {job.processed_at ? new Date(job.processed_at * 1000).toLocaleString() : 'Recently'}
                              </span>
                            </div>
                          </div>
                          <div className="results-count">
                            <span className="total-count">{totalVulnerabilities} vulnerabilities</span>
                          </div>
                        </div>

                        <div className="severity-summary">
                          <div className="severity-stats">
                            {severityCounts.HIGH > 0 && (
                              <span className="severity-badge high">
                                🔴 High: {severityCounts.HIGH}
                              </span>
                            )}
                            {severityCounts.MEDIUM > 0 && (
                              <span className="severity-badge medium">
                                🟡 Medium: {severityCounts.MEDIUM}
                              </span>
                            )}
                            {severityCounts.LOW > 0 && (
                              <span className="severity-badge low">
                                🟢 Low: {severityCounts.LOW}
                              </span>
                            )}
                            {Object.keys(severityCounts).length === 0 && (
                              <span className="no-vulnerabilities">✅ No vulnerabilities</span>
                            )}
                          </div>
                        </div>

                        {vulnerabilities.length > 0 && (
                          <div className="vulnerabilities-preview">
                            <h6>🔸 Vulnerability Preview:</h6>
                            <div className="vuln-preview-list">
                              {vulnerabilities.slice(0, 3).map((vuln, vIndex) => {
                                const cve = vuln.cve || {};
                                const severity = cve.metrics?.cvssMetricV2?.[0]?.baseSeverity || 'UNKNOWN';
                                const score = cve.metrics?.cvssMetricV2?.[0]?.cvssData?.baseScore || 'N/A';
                                const description = cve.descriptions?.[0]?.value || 'No description';

                                return (
                                  <div key={vIndex} className="vuln-preview-item">
                                    <div className="vuln-preview-header">
                                      <strong className="cve-id-small">{cve.id}</strong>
                                      <span className={`severity-badge-small ${severity.toLowerCase()}`}>
                                        {severity} ({score})
                                      </span>
                                    </div>
                                    <div className="vuln-preview-desc">
                                      {description.length > 80 ? 
                                        description.substring(0, 80) + '...' : 
                                        description
                                      }
                                    </div>
                                  </div>
                                );
                              })}
                              {vulnerabilities.length > 3 && (
                                <div className="more-vulns-indicator">
                                  <span>... and {vulnerabilities.length - 3} more vulnerabilities</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        <div className="card-footer">
                          <div className="processed-info">
                            <span className="processed-via">
                              🚀 Processed via: {job.processed_via || 'queue_consumer'}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
