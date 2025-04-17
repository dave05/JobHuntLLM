import React, { useState } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  Button, 
  TextField, 
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
  Chip
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import WorkIcon from '@mui/icons-material/Work';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

function JobsPage() {
  const { currentUser } = useAuth();
  
  const [source, setSource] = useState('csv');
  const [query, setQuery] = useState('software engineer');
  const [location, setLocation] = useState('remote');
  const [limit, setLimit] = useState(10);
  const [apiKey, setApiKey] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [fetchedJobs, setFetchedJobs] = useState(null);
  const [jobsHistory, setJobsHistory] = useState([]);

  const handleFetchJobs = async () => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      
      const response = await axios.post('/jobs/fetch', {
        source,
        query,
        location,
        limit,
        api_key: apiKey || undefined
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setFetchedJobs(response.data);
      setJobsHistory([response.data, ...jobsHistory]);
      setSuccess(`Successfully fetched ${response.data.jobs.length} jobs!`);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setError('Failed to fetch jobs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Job Search
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Search Parameters
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel id="source-label">Source</InputLabel>
              <Select
                labelId="source-label"
                id="source"
                value={source}
                label="Source"
                onChange={(e) => setSource(e.target.value)}
              >
                <MenuItem value="csv">CSV File</MenuItem>
                <MenuItem value="json">JSON File</MenuItem>
                <MenuItem value="linkedin">LinkedIn</MenuItem>
                <MenuItem value="indeed">Indeed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Query or File Path"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              helperText={source === 'csv' || source === 'json' ? 'Enter file path' : 'Enter search query'}
            />
          </Grid>
          
          {(source === 'linkedin' || source === 'indeed') && (
            <>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="API Key (Optional)"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </Grid>
            </>
          )}
          
          <Grid item xs={12}>
            <Typography gutterBottom>
              Limit: {limit} jobs
            </Typography>
            <Slider
              value={limit}
              onChange={(e, newValue) => setLimit(newValue)}
              aria-labelledby="limit-slider"
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
              startIcon={<SearchIcon />}
              onClick={handleFetchJobs}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Fetch Jobs'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {fetchedJobs && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Fetched Jobs
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            Jobs ID: {fetchedJobs.jobs_id}
          </Typography>
          
          <List>
            {fetchedJobs.jobs.map((job, index) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <WorkIcon sx={{ mr: 1 }} />
                      <Typography variant="h6">{job.title}</Typography>
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body1">{job.company} • {job.location}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {job.description.length > 200 
                          ? job.description.substring(0, 200) + '...' 
                          : job.description}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip 
                          label={`Posted: ${job.date_posted}`} 
                          size="small" 
                          sx={{ mr: 1 }} 
                        />
                        {job.salary && (
                          <Chip 
                            label={`Salary: ${job.salary}`} 
                            size="small" 
                            sx={{ mr: 1 }} 
                          />
                        )}
                        {job.job_type && (
                          <Chip 
                            label={job.job_type} 
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
      
      {jobsHistory.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Job Search History
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={2}>
            {jobsHistory.map((item, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {item.jobs_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.jobs.length} jobs from {item.jobs[0]?.source || 'unknown'}
                    </Typography>
                    <Typography variant="body2">
                      Top companies: {item.jobs.slice(0, 3).map(job => job.company).join(', ')}
                      {item.jobs.length > 3 ? '...' : ''}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" onClick={() => setFetchedJobs(item)}>
                      View Jobs
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

export default JobsPage;
