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
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Switch,
  FormControlLabel
} from '@mui/material';
import EventIcon from '@mui/icons-material/Event';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

function SchedulePage() {
  const { currentUser } = useAuth();
  
  const [jobId, setJobId] = useState('');
  const [daysAfter, setDaysAfter] = useState(7);
  const [useGoogleCalendar, setUseGoogleCalendar] = useState(false);
  const [credentialsPath, setCredentialsPath] = useState('');
  const [tokenPath, setTokenPath] = useState('');
  
  const [jobs, setJobs] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [scheduledEvents, setScheduledEvents] = useState([]);

  // Fetch jobs
  useEffect(() => {
    // In a real application, you would fetch these from the API
    // For now, we'll use dummy data
    setJobs([
      { id: 'job1', title: 'Software Engineer', company: 'Example Corp' },
      { id: 'job2', title: 'Data Scientist', company: 'Data Inc' }
    ]);
    
    // Fetch scheduled events
    setScheduledEvents([
      { 
        id: 'event1', 
        type: 'application', 
        company: 'Example Corp', 
        job_title: 'Software Engineer',
        date: '2023-07-10' 
      },
      { 
        id: 'event2', 
        type: 'followup', 
        company: 'Example Corp', 
        job_title: 'Software Engineer',
        date: '2023-07-17' 
      }
    ]);
  }, []);

  const handleSchedule = async () => {
    if (!jobId) {
      setError('Please select a job');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      
      const requestData = {
        job_id: jobId,
        days_after: daysAfter,
        use_google_calendar: useGoogleCalendar
      };
      
      if (useGoogleCalendar) {
        if (!credentialsPath) {
          setError('Please provide a credentials path for Google Calendar');
          setLoading(false);
          return;
        }
        
        requestData.credentials_path = credentialsPath;
        requestData.token_path = tokenPath || undefined;
      }
      
      const response = await axios.post('/schedule', requestData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      // Add new events to the list
      const selectedJob = jobs.find(job => job.id === jobId);
      const newEvents = [
        {
          id: response.data.application_id,
          type: 'application',
          company: selectedJob.company,
          job_title: selectedJob.title,
          date: new Date().toISOString().split('T')[0]
        },
        {
          id: response.data.followup_id,
          type: 'followup',
          company: selectedJob.company,
          job_title: selectedJob.title,
          date: new Date(new Date().setDate(new Date().getDate() + daysAfter)).toISOString().split('T')[0]
        }
      ];
      
      setScheduledEvents([...newEvents, ...scheduledEvents]);
      setSuccess('Events scheduled successfully!');
    } catch (error) {
      console.error('Error scheduling events:', error);
      setError('Failed to schedule events. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Schedule Events
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Schedule Application and Follow-up
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel id="job-label">Job</InputLabel>
              <Select
                labelId="job-label"
                id="job"
                value={jobId}
                label="Job"
                onChange={(e) => setJobId(e.target.value)}
              >
                {jobs.map((job) => (
                  <MenuItem key={job.id} value={job.id}>
                    {job.title} at {job.company}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Days After Application for Follow-up"
              type="number"
              value={daysAfter}
              onChange={(e) => setDaysAfter(parseInt(e.target.value))}
              InputProps={{ inputProps: { min: 1, max: 30 } }}
            />
          </Grid>
          
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={useGoogleCalendar}
                  onChange={(e) => setUseGoogleCalendar(e.target.checked)}
                />
              }
              label="Use Google Calendar"
            />
          </Grid>
          
          {useGoogleCalendar && (
            <>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Google Calendar Credentials Path"
                  value={credentialsPath}
                  onChange={(e) => setCredentialsPath(e.target.value)}
                  required
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Google Calendar Token Path (Optional)"
                  value={tokenPath}
                  onChange={(e) => setTokenPath(e.target.value)}
                />
              </Grid>
            </>
          )}
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<EventIcon />}
              onClick={handleSchedule}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Schedule Events'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {scheduledEvents.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Scheduled Events
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <List>
            {scheduledEvents.map((event) => (
              <ListItem key={event.id} divider>
                <ListItemIcon>
                  {event.type === 'application' ? <CalendarMonthIcon /> : <NotificationsActiveIcon />}
                </ListItemIcon>
                <ListItemText
                  primary={`${event.type === 'application' ? 'Application' : 'Follow-up'} for ${event.job_title} at ${event.company}`}
                  secondary={`Scheduled for ${event.date}`}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
}

export default SchedulePage;
