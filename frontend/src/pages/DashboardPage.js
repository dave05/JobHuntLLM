import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  CardActions,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

function DashboardPage() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dashboardData, setDashboardData] = useState({
    resumes: [],
    jobs: [],
    rankedJobs: [],
    emails: [],
    scheduledEvents: []
  });

  useEffect(() => {
    // In a real application, you would fetch dashboard data from the API
    // For now, we'll simulate loading and then set some dummy data
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError('');
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Set dummy data
        setDashboardData({
          resumes: [
            { id: 'resume1', name: 'My Resume', date: '2023-05-01' }
          ],
          jobs: [
            { id: 'jobs1', source: 'linkedin', count: 25, date: '2023-05-02' }
          ],
          rankedJobs: [
            { id: 'ranked1', count: 10, date: '2023-05-02' }
          ],
          emails: [
            { id: 'email1', type: 'cover_letter', company: 'Example Corp', date: '2023-05-03' }
          ],
          scheduledEvents: [
            { id: 'event1', type: 'application', company: 'Example Corp', date: '2023-05-03' }
          ]
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Typography variant="h6" gutterBottom>
        Welcome, {currentUser?.full_name || currentUser?.username}!
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button 
                    variant="contained" 
                    fullWidth
                    onClick={() => navigate('/resume')}
                  >
                    Upload Resume
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button 
                    variant="contained" 
                    fullWidth
                    onClick={() => navigate('/jobs')}
                  >
                    Find Jobs
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button 
                    variant="contained" 
                    fullWidth
                    onClick={() => navigate('/match')}
                  >
                    Match Jobs
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button 
                    variant="contained" 
                    fullWidth
                    onClick={() => navigate('/email')}
                  >
                    Compose Email
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                {dashboardData.resumes.length > 0 && (
                  <ListItem>
                    <ListItemText 
                      primary="Resume Uploaded" 
                      secondary={`${dashboardData.resumes[0].name} on ${dashboardData.resumes[0].date}`} 
                    />
                  </ListItem>
                )}
                
                {dashboardData.jobs.length > 0 && (
                  <ListItem>
                    <ListItemText 
                      primary="Jobs Fetched" 
                      secondary={`${dashboardData.jobs[0].count} jobs from ${dashboardData.jobs[0].source} on ${dashboardData.jobs[0].date}`} 
                    />
                  </ListItem>
                )}
                
                {dashboardData.rankedJobs.length > 0 && (
                  <ListItem>
                    <ListItemText 
                      primary="Jobs Ranked" 
                      secondary={`${dashboardData.rankedJobs[0].count} jobs on ${dashboardData.rankedJobs[0].date}`} 
                    />
                  </ListItem>
                )}
                
                {dashboardData.emails.length > 0 && (
                  <ListItem>
                    <ListItemText 
                      primary="Email Composed" 
                      secondary={`${dashboardData.emails[0].type.replace('_', ' ')} for ${dashboardData.emails[0].company} on ${dashboardData.emails[0].date}`} 
                    />
                  </ListItem>
                )}
                
                {dashboardData.scheduledEvents.length > 0 && (
                  <ListItem>
                    <ListItemText 
                      primary="Event Scheduled" 
                      secondary={`${dashboardData.scheduledEvents[0].type} for ${dashboardData.scheduledEvents[0].company} on ${dashboardData.scheduledEvents[0].date}`} 
                    />
                  </ListItem>
                )}
                
                {Object.values(dashboardData).every(arr => arr.length === 0) && (
                  <ListItem>
                    <ListItemText 
                      primary="No recent activity" 
                      secondary="Start by uploading your resume or finding jobs" 
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Job Search Progress
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap' }}>
                <Box sx={{ textAlign: 'center', m: 2 }}>
                  <Typography variant="h4" color="primary">
                    {dashboardData.resumes.length}
                  </Typography>
                  <Typography variant="body2">Resumes</Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', m: 2 }}>
                  <Typography variant="h4" color="primary">
                    {dashboardData.jobs.reduce((total, job) => total + job.count, 0)}
                  </Typography>
                  <Typography variant="body2">Jobs Found</Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', m: 2 }}>
                  <Typography variant="h4" color="primary">
                    {dashboardData.rankedJobs.reduce((total, job) => total + job.count, 0)}
                  </Typography>
                  <Typography variant="body2">Jobs Matched</Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', m: 2 }}>
                  <Typography variant="h4" color="primary">
                    {dashboardData.emails.length}
                  </Typography>
                  <Typography variant="body2">Emails Composed</Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', m: 2 }}>
                  <Typography variant="h4" color="primary">
                    {dashboardData.scheduledEvents.length}
                  </Typography>
                  <Typography variant="body2">Events Scheduled</Typography>
                </Box>
              </Box>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/resume')}>Manage Resumes</Button>
              <Button size="small" onClick={() => navigate('/jobs')}>View Jobs</Button>
              <Button size="small" onClick={() => navigate('/email')}>View Emails</Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default DashboardPage;
