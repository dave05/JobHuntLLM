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
  CircularProgress,
  Alert,
  TextField,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import DescriptionIcon from '@mui/icons-material/Description';
import ReplyIcon from '@mui/icons-material/Reply';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

function EmailPage() {
  const { currentUser } = useAuth();
  
  const [resumeId, setResumeId] = useState('');
  const [jobId, setJobId] = useState('');
  const [emailType, setEmailType] = useState('cover');
  
  const [resumes, setResumes] = useState([]);
  const [jobs, setJobs] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [email, setEmail] = useState(null);
  const [emailHistory, setEmailHistory] = useState([]);

  // Fetch resumes and jobs
  useEffect(() => {
    // In a real application, you would fetch these from the API
    // For now, we'll use dummy data
    setResumes([
      { id: 'resume1', name: 'My Resume' }
    ]);
    
    setJobs([
      { id: 'job1', title: 'Software Engineer', company: 'Example Corp' },
      { id: 'job2', title: 'Data Scientist', company: 'Data Inc' }
    ]);
  }, []);

  const handleEmailTypeChange = (event, newType) => {
    if (newType !== null) {
      setEmailType(newType);
    }
  };

  const handleComposeEmail = async () => {
    if (!resumeId) {
      setError('Please select a resume');
      return;
    }
    
    if (!jobId) {
      setError('Please select a job');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const token = localStorage.getItem('token');
      
      const response = await axios.post('/email/compose', {
        resume_id: resumeId,
        job_id: jobId,
        email_type: emailType
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setEmail(response.data);
      setEmailHistory([response.data, ...emailHistory]);
      setSuccess(`Successfully composed ${emailType} letter!`);
    } catch (error) {
      console.error('Error composing email:', error);
      setError('Failed to compose email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Email Composition
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Compose Email
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
          
          <Grid item xs={12}>
            <Typography gutterBottom>
              Email Type:
            </Typography>
            <ToggleButtonGroup
              value={emailType}
              exclusive
              onChange={handleEmailTypeChange}
              aria-label="email type"
            >
              <ToggleButton value="cover" aria-label="cover letter">
                <DescriptionIcon sx={{ mr: 1 }} />
                Cover Letter
              </ToggleButton>
              <ToggleButton value="followup" aria-label="follow-up email">
                <ReplyIcon sx={{ mr: 1 }} />
                Follow-up Email
              </ToggleButton>
            </ToggleButtonGroup>
          </Grid>
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<EmailIcon />}
              onClick={handleComposeEmail}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Compose Email'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {email && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            {emailType === 'cover' ? 'Cover Letter' : 'Follow-up Email'}
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            Email ID: {email.email_id}
          </Typography>
          
          <TextField
            fullWidth
            multiline
            rows={15}
            value={email.email}
            InputProps={{
              readOnly: true,
            }}
            variant="outlined"
            sx={{ mb: 2, fontFamily: 'monospace' }}
          />
          
          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              navigator.clipboard.writeText(email.email);
              setSuccess('Email copied to clipboard!');
            }}
          >
            Copy to Clipboard
          </Button>
        </Paper>
      )}
      
      {emailHistory.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Email History
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={2}>
            {emailHistory.map((item, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {item.email_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.email_id.includes('cover_letter') ? 'Cover Letter' : 'Follow-up Email'}
                    </Typography>
                    <Typography variant="body2">
                      {item.email.substring(0, 100)}...
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" onClick={() => setEmail(item)}>
                      View Email
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

export default EmailPage;
