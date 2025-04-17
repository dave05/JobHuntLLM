import React from 'react';
import { Typography, Button, Box, Paper, Grid, Card, CardContent, CardMedia } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          mb: 4, 
          textAlign: 'center',
          backgroundImage: 'linear-gradient(to right, #1976d2, #64b5f6)',
          color: 'white'
        }}
      >
        <Typography variant="h2" component="h1" gutterBottom>
          JobHuntGPT
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          An LLM-powered job search assistant
        </Typography>
        <Box sx={{ mt: 4 }}>
          {!isAuthenticated ? (
            <>
              <Button 
                variant="contained" 
                color="secondary" 
                size="large" 
                onClick={() => navigate('/register')}
                sx={{ mr: 2 }}
              >
                Get Started
              </Button>
              <Button 
                variant="outlined" 
                color="inherit" 
                size="large" 
                onClick={() => navigate('/login')}
              >
                Login
              </Button>
            </>
          ) : (
            <Button 
              variant="contained" 
              color="secondary" 
              size="large" 
              onClick={() => navigate('/dashboard')}
            >
              Go to Dashboard
            </Button>
          )}
        </Box>
      </Paper>

      <Typography variant="h4" component="h2" gutterBottom>
        Features
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardMedia
              component="div"
              sx={{
                height: 140,
                backgroundColor: '#1976d2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '3rem'
              }}
            >
              📄
            </CardMedia>
            <CardContent>
              <Typography gutterBottom variant="h5" component="div">
                Resume Parsing
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Extract skills, experience, and education from your resume automatically.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardMedia
              component="div"
              sx={{
                height: 140,
                backgroundColor: '#1976d2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '3rem'
              }}
            >
              🔍
            </CardMedia>
            <CardContent>
              <Typography gutterBottom variant="h5" component="div">
                Job Matching
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Find the best job matches based on your skills and experience.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardMedia
              component="div"
              sx={{
                height: 140,
                backgroundColor: '#1976d2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '3rem'
              }}
            >
              ✉️
            </CardMedia>
            <CardContent>
              <Typography gutterBottom variant="h5" component="div">
                Email Composition
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Generate tailored cover letters and follow-up emails.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardMedia
              component="div"
              sx={{
                height: 140,
                backgroundColor: '#1976d2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '3rem'
              }}
            >
              📅
            </CardMedia>
            <CardContent>
              <Typography gutterBottom variant="h5" component="div">
                Scheduling
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Schedule reminders and follow-ups for job applications.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardMedia
              component="div"
              sx={{
                height: 140,
                backgroundColor: '#1976d2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '3rem'
              }}
            >
              🤖
            </CardMedia>
            <CardContent>
              <Typography gutterBottom variant="h5" component="div">
                AI-Powered
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Leverages LLM technology to provide intelligent job search assistance.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardMedia
              component="div"
              sx={{
                height: 140,
                backgroundColor: '#1976d2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '3rem'
              }}
            >
              🔄
            </CardMedia>
            <CardContent>
              <Typography gutterBottom variant="h5" component="div">
                Workflow Automation
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Automate your entire job search workflow from resume to follow-up.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h4" component="h2" gutterBottom>
        How It Works
      </Typography>
      
      <Paper elevation={1} sx={{ p: 3, mb: 4 }}>
        <Typography variant="body1" paragraph>
          JobHuntGPT uses advanced AI technology to streamline your job search process. Here's how it works:
        </Typography>
        
        <Typography variant="body1" component="ol" sx={{ pl: 2 }}>
          <li>Upload your resume or enter your skills and experience</li>
          <li>Search for jobs or import job listings from various sources</li>
          <li>Our AI matches your profile with job requirements</li>
          <li>Generate customized cover letters for your top matches</li>
          <li>Schedule follow-ups and track your applications</li>
        </Typography>
        
        <Box sx={{ mt: 2 }}>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={() => isAuthenticated ? navigate('/dashboard') : navigate('/register')}
          >
            {isAuthenticated ? 'Go to Dashboard' : 'Get Started'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}

export default HomePage;
