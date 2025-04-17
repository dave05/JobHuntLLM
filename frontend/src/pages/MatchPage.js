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
  Slider,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip,
  LinearProgress
} from '@mui/material';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import WorkIcon from '@mui/icons-material/Work';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

function MatchPage() {
  const { currentUser } = useAuth();
  
  const [resumeId, setResumeId] = useState('');
  const [jobsId, setJobsId] = useState('');
  const [topK, setTopK] = useState(10);
  
  const [resumes, setResumes] = useState([]);
  const [jobSets, setJobSets] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [rankedJobs, setRankedJobs] = useState(null);
  const [matchHistory, setMatchHistory] = useState([]);

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

  const handleRankJobs = async () => {
    if (!resumeId) {
      setError('Please select a resume');
      return;
    }
    
    if (!jobsId) {
      setError('Please select a job set');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      
      const response = await axios.post('/jobs/rank', {
        resume_id: resumeId,
        jobs_id: jobsId,
        top_k: topK
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setRankedJobs(response.data);
      setMatchHistory([response.data, ...matchHistory]);
      setSuccess(`Successfully ranked ${response.data.ranked_jobs.length} jobs!`);
    } catch (error) {
      console.error('Error ranking jobs:', error);
      setError('Failed to rank jobs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Job Matching
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Match Parameters
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
            <Typography gutterBottom>
              Top K: {topK} jobs
            </Typography>
            <Slider
              value={topK}
              onChange={(e, newValue) => setTopK(newValue)}
              aria-labelledby="top-k-slider"
              valueLabelDisplay="auto"
              step={5}
              marks
              min={5}
              max={50}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<CompareArrowsIcon />}
              onClick={handleRankJobs}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Rank Jobs'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {rankedJobs && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Ranked Jobs
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            Ranked Jobs ID: {rankedJobs.ranked_jobs_id}
          </Typography>
          
          <List>
            {rankedJobs.ranked_jobs.map((item, index) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <WorkIcon sx={{ mr: 1 }} />
                        <Typography variant="h6">{item.job.title}</Typography>
                      </Box>
                      <Chip 
                        label={`Match: ${(item.similarity * 100).toFixed(0)}%`} 
                        color={item.similarity > 0.7 ? 'success' : item.similarity > 0.5 ? 'primary' : 'default'}
                      />
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body1">{item.job.company} • {item.job.location}</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, mb: 1 }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={item.similarity * 100} 
                            color={item.similarity > 0.7 ? 'success' : item.similarity > 0.5 ? 'primary' : 'inherit'}
                          />
                        </Box>
                        <Box sx={{ minWidth: 35 }}>
                          <Typography variant="body2" color="text.secondary">{`${(item.similarity * 100).toFixed(0)}%`}</Typography>
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {item.job.description.length > 200 
                          ? item.job.description.substring(0, 200) + '...' 
                          : item.job.description}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip 
                          label={`Posted: ${item.job.date_posted}`} 
                          size="small" 
                          sx={{ mr: 1 }} 
                        />
                        {item.job.salary && (
                          <Chip 
                            label={`Salary: ${item.job.salary}`} 
                            size="small" 
                            sx={{ mr: 1 }} 
                          />
                        )}
                        {item.job.job_type && (
                          <Chip 
                            label={item.job.job_type} 
                            size="small" 
                          />
                        )}
                      </Box>
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
      
      {matchHistory.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Match History
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={2}>
            {matchHistory.map((item, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {item.ranked_jobs_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.ranked_jobs.length} ranked jobs
                    </Typography>
                    <Typography variant="body2">
                      Top match: {item.ranked_jobs[0]?.job.title} at {item.ranked_jobs[0]?.job.company} 
                      ({(item.ranked_jobs[0]?.similarity * 100).toFixed(0)}%)
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" onClick={() => setRankedJobs(item)}>
                      View Matches
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

export default MatchPage;
