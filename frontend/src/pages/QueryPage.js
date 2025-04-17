import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  Button, 
  Divider,
  Grid,
  Card,
  CardContent,
  CardActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  CircularProgress,
  Alert
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

function QueryPage() {
  const { currentUser } = useAuth();
  
  const [resumeId, setResumeId] = useState('');
  const [jobsId, setJobsId] = useState('');
  const [queryText, setQueryText] = useState('');
  const [modelPath, setModelPath] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState('all-MiniLM-L6-v2');
  
  const [resumes, setResumes] = useState([]);
  const [jobSets, setJobSets] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [queryResponse, setQueryResponse] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);

  // Fetch resumes and job sets
  useEffect(() => {
    // In a real application, you would fetch these from the API
    // For now, we'll use dummy data
    setResumes([
      { id: 'resume1', name: 'My Resume' }
    ]);
    
    setJobSets([
      { id: 'jobs1', source: 'linkedin', count: 25 }
    ]);
  }, []);

  const handleQuery = async () => {
    if (!resumeId) {
      setError('Please select a resume');
      return;
    }
    
    if (!jobsId) {
      setError('Please select a job set');
      return;
    }
    
    if (!queryText.trim()) {
      setError('Please enter a query');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      
      const response = await axios.post('/query', {
        resume_id: resumeId,
        jobs_id: jobsId,
        query_text: queryText,
        model_path: modelPath || undefined,
        embedding_model: embeddingModel
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setQueryResponse(response.data);
      setQueryHistory([response.data, ...queryHistory]);
      setSuccess('Query executed successfully!');
    } catch (error) {
      console.error('Error executing query:', error);
      setError('Failed to execute query. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Semantic Search
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Query Parameters
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel id="resume-label">Resume</InputLabel>
              <Select
                labelId="resume-label"
                id="resume"
                value={resumeId}
                label="Resume"
                onChange={(e) => setResumeId(e.target.value)}
              >
                {resumes.map((resume) => (
                  <MenuItem key={resume.id} value={resume.id}>
                    {resume.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel id="jobs-label">Job Set</InputLabel>
              <Select
                labelId="jobs-label"
                id="jobs"
                value={jobsId}
                label="Job Set"
                onChange={(e) => setJobsId(e.target.value)}
              >
                {jobSets.map((jobSet) => (
                  <MenuItem key={jobSet.id} value={jobSet.id}>
                    {jobSet.id} ({jobSet.count} jobs from {jobSet.source})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Query"
              multiline
              rows={3}
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Enter your query here, e.g., 'What are the best job matches for someone with Python and machine learning skills?'"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="LLaMA Model Path (Optional)"
              value={modelPath}
              onChange={(e) => setModelPath(e.target.value)}
              placeholder="Path to your LLaMA model"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Embedding Model"
              value={embeddingModel}
              onChange={(e) => setEmbeddingModel(e.target.value)}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<SearchIcon />}
              onClick={handleQuery}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Execute Query'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {queryResponse && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Query Response
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            Query: {queryResponse.query}
          </Typography>
          
          <TextField
            fullWidth
            multiline
            rows={10}
            value={queryResponse.response}
            InputProps={{
              readOnly: true,
            }}
            variant="outlined"
            sx={{ mb: 2 }}
          />
        </Paper>
      )}
      
      {queryHistory.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Query History
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={2}>
            {queryHistory.map((item, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom noWrap>
                      {item.query}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {item.response.substring(0, 100)}...
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" onClick={() => setQueryResponse(item)}>
                      View Response
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Box>
  );
}

export default QueryPage;
