import React, { useState, useEffect, useRef } from 'react';

const LandslideReportUploader = ({ apiBaseUrl = 'http://localhost:8000' }) => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [lat, setLat] = useState('');
  const [lng, setLng] = useState('');
  const [locationError, setLocationError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reportId, setReportId] = useState(null);
  const [pipelineState, setPipelineState] = useState(''); // 'idle', 'processing', 'assessing', 'posted', 'rejected', 'error'
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Capture Geolocation on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLat(position.coords.latitude.toFixed(6));
          setLng(position.coords.longitude.toFixed(6));
          setLocationError('');
        },
        (error) => {
          setLocationError('GPS permission denied or unavailable. Please enter coordinates manually.');
        }
      );
    } else {
      setLocationError('Geolocation is not supported by your browser.');
    }
    
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      const objectUrl = URL.createObjectURL(selectedFile);
      setPreview(objectUrl);
      resetState();
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      setFile(droppedFile);
      const objectUrl = URL.createObjectURL(droppedFile);
      setPreview(objectUrl);
      resetState();
    }
  };

  const resetState = () => {
    setReportId(null);
    setPipelineState('idle');
    setResult(null);
    setErrorMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setErrorMessage('Please select an image first.');
      return;
    }
    if (!lat || !lng) {
      setErrorMessage('Location coordinates are required.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');
    setPipelineState('processing');

    const formData = new FormData();
    formData.append('image', file);
    formData.append('latitude', lat);
    formData.append('longitude', lng);
    formData.append('device_timestamp', new Date().toISOString());

    try {
      const res = await fetch(`${apiBaseUrl}/api/report`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Failed to upload report');

      const data = await res.json();
      setReportId(data.id);
      startPolling(data.id);
    } catch (err) {
      setErrorMessage(err.message || 'Upload failed due to network error.');
      setIsSubmitting(false);
      setPipelineState('error');
    }
  };

  const startPolling = (id) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    
    let assessStateTriggered = false;

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/alerts/${id}`);
        if (!res.ok) return; // Keep trying if 404 momentarily
        
        const data = await res.json();
        setResult(data);

        if (data.status === 'processing') {
          // If we have AI check results but not severity yet, we are in 'assessing' phase
          if (data.is_ai_generated === false && !assessStateTriggered) {
            setPipelineState('assessing');
            assessStateTriggered = true;
          } else {
            setPipelineState('processing');
          }
        } else if (data.status === 'posted') {
          setPipelineState('posted');
          setIsSubmitting(false);
          clearInterval(pollIntervalRef.current);
        } else if (data.status === 'rejected') {
          setPipelineState('rejected');
          setIsSubmitting(false);
          clearInterval(pollIntervalRef.current);
        } else if (data.status === 'error') {
          setPipelineState('error');
          setErrorMessage('Pipeline encountered an error while processing the image.');
          setIsSubmitting(false);
          clearInterval(pollIntervalRef.current);
        }
      } catch (err) {
        console.error('Polling error', err);
      }
    }, 2000);
  };

  const styles = {
    container: {
      maxWidth: '450px',
      margin: '0 auto',
      padding: '24px',
      borderRadius: '16px',
      background: 'rgba(255, 255, 255, 0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      color: '#fff',
      fontFamily: "'Inter', sans-serif",
    },
    title: {
      fontSize: '24px',
      fontWeight: '600',
      marginBottom: '20px',
      textAlign: 'center',
      background: 'linear-gradient(90deg, #ff8a00, #e52e71)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    dropZone: {
      border: '2px dashed rgba(255,255,255,0.3)',
      borderRadius: '12px',
      padding: '30px',
      textAlign: 'center',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      background: 'rgba(0,0,0,0.2)',
      marginBottom: '20px',
      position: 'relative',
      overflow: 'hidden',
    },
    previewImage: {
      width: '100%',
      maxHeight: '200px',
      objectFit: 'cover',
      borderRadius: '8px',
      marginTop: '10px',
    },
    inputGroup: {
      marginBottom: '15px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
    },
    label: {
      fontSize: '14px',
      color: 'rgba(255,255,255,0.7)',
    },
    input: {
      background: 'rgba(0,0,0,0.3)',
      border: '1px solid rgba(255,255,255,0.2)',
      borderRadius: '8px',
      padding: '12px',
      color: '#fff',
      fontSize: '16px',
      outline: 'none',
      transition: 'border-color 0.3s ease',
    },
    button: {
      width: '100%',
      padding: '14px',
      borderRadius: '8px',
      border: 'none',
      background: 'linear-gradient(90deg, #ff8a00, #e52e71)',
      color: '#fff',
      fontSize: '16px',
      fontWeight: '600',
      cursor: 'pointer',
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      marginTop: '10px',
    },
    errorText: {
      color: '#ff4b4b',
      fontSize: '14px',
      marginTop: '5px',
    },
    statusCard: {
      marginTop: '20px',
      padding: '16px',
      borderRadius: '12px',
      background: 'rgba(0,0,0,0.4)',
      border: '1px solid rgba(255,255,255,0.1)',
    },
    badge: (severity) => {
      const colors = {
        LOW: '#4ade80',
        MEDIUM: '#facc15',
        HIGH: '#fb923c',
        CRITICAL: '#ef4444',
      };
      return {
        display: 'inline-block',
        padding: '4px 10px',
        borderRadius: '20px',
        fontSize: '12px',
        fontWeight: 'bold',
        background: colors[severity] || '#aaa',
        color: '#000',
      };
    },
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Report a Landslide</h2>
      
      <form onSubmit={handleSubmit}>
        <div 
          style={styles.dropZone}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          {preview ? (
            <img src={preview} alt="Preview" style={styles.previewImage} />
          ) : (
            <div>
              <div style={{ fontSize: '32px', marginBottom: '10px' }}>📸</div>
              <p style={{ margin: 0, color: 'rgba(255,255,255,0.8)' }}>Drag & drop or tap to upload</p>
            </div>
          )}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/*" 
            style={{ display: 'none' }} 
          />
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Latitude</label>
            <input 
              style={styles.input} 
              type="text" 
              value={lat} 
              onChange={(e) => setLat(e.target.value)} 
              placeholder="e.g. 34.0522" 
            />
          </div>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Longitude</label>
            <input 
              style={styles.input} 
              type="text" 
              value={lng} 
              onChange={(e) => setLng(e.target.value)} 
              placeholder="e.g. -118.2437" 
            />
          </div>
        </div>
        
        {locationError && <div style={styles.errorText}>{locationError}</div>}
        {errorMessage && <div style={styles.errorText}>{errorMessage}</div>}

        <button 
          type="submit" 
          style={{
            ...styles.button,
            opacity: isSubmitting || !file ? 0.6 : 1,
            cursor: isSubmitting || !file ? 'not-allowed' : 'pointer',
          }}
          disabled={isSubmitting || !file}
        >
          {isSubmitting ? 'Uploading...' : 'Submit Report'}
        </button>
      </form>

      {pipelineState !== 'idle' && (
        <div style={styles.statusCard}>
          {pipelineState === 'processing' && <p>🔍 Checking image authenticity...</p>}
          {pipelineState === 'assessing' && <p>⚠️ Authenticated! Assessing severity...</p>}
          
          {pipelineState === 'posted' && result && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h3 style={{ margin: 0, color: '#fff' }}>Alert Posted</h3>
                <span style={styles.badge(result.severity)}>{result.severity}</span>
              </div>
              <p style={{ fontSize: '14px', color: '#ccc', margin: '5px 0' }}>
                <strong>Confidence:</strong> {result.severity_confidence}%
              </p>
              <p style={{ fontSize: '14px', color: '#ccc', margin: '5px 0' }}>
                <strong>Action:</strong> {result.recommended_action}
              </p>
            </div>
          )}

          {pipelineState === 'rejected' && result && (
            <div>
              <h3 style={{ margin: '0 0 10px 0', color: '#ff4b4b' }}>Submission Rejected</h3>
              <p style={{ fontSize: '14px', color: '#ccc' }}>
                Our systems flagged this image as potentially AI-generated (Confidence: {result.ai_confidence}%).
              </p>
              <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', marginTop: '5px' }}>
                Reason: {result.ai_reasoning}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LandslideReportUploader;
