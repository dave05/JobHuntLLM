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
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
  Tab,
  Tabs
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`resume-tabpanel-${index}`}
      aria-labelledby={`resume-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function ResumePage() {
  const { currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState(0);
  
  const [file, setFile] = useState(null);
  const [resumeText, setResumeText] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [parsedResume, setParsedResume] = useState(null);
  const [resumeHistory, setResumeHistory] = useState([]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleUploadResume = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const formData = new FormData();
      formData.append('resume_file', file);
      
      const token = localStorage.getItem('token');
      
      const response = await axios.post('/resume/parse', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      });
      
      setParsedResume(response.data.resume);
      setResumeHistory([response.data, ...resumeHistory]);
      setSuccess('Resume uploaded and parsed successfully!');
    } catch (error) {
      console.error('Error uploading resume:', error);
      setError('Failed to upload and parse resume. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitText = async () => {
    if (!resumeText.trim()) {
      setError('Please enter your resume text');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const formData = new FormData();
      formData.append('resume_text', resumeText);
      
      const token = localStorage.getItem('token');
      
      const response = await axios.post('/resume/parse', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      });
      
      setParsedResume(response.data.resume);
      setResumeHistory([response.data, ...resumeHistory]);
      setSuccess('Resume text parsed successfully!');
    } catch (error) {
      console.error('Error parsing resume text:', error);
      setError('Failed to parse resume text. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Resume Management
      </Typography>
      
      <Paper sx={{ mb: 4 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
        >
          <Tab icon={<UploadFileIcon />} label="Upload Resume" />
          <Tab icon={<TextFieldsIcon />} label="Enter Text" />
        </Tabs>
        
        <TabPanel value={activeTab} index={0}>
          <Box sx={{ p: 2 }}>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
            
            <Box sx={{ mb: 3 }}>
              <input
                accept=".pdf,.doc,.docx,.txt"
                style={{ display: 'none' }}
                id="resume-file"
                type="file"
                onChange={handleFileChange}
              />
              <label htmlFor="resume-file">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<UploadFileIcon />}
                >
                  Select Resume File
                </Button>
              </label>
              {file && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Selected file: {file.name}
                </Typography>
              )}
            </Box>
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleUploadResume}
              disabled={!file || loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Upload and Parse'}
            </Button>
          </Box>
        </TabPanel>
        
        <TabPanel value={activeTab} index={1}>
          <Box sx={{ p: 2 }}>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
            
            <TextField
              label="Paste your resume text here"
              multiline
              rows={10}
              fullWidth
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              sx={{ mb: 3 }}
            />
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmitText}
              disabled={!resumeText.trim() || loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Parse Resume Text'}
            </Button>
          </Box>
        </TabPanel>
      </Paper>
      
      {parsedResume && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            Parsed Resume
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle1">Name:</Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>{parsedResume.name || 'N/A'}</Typography>
              
              <Typography variant="subtitle1">Email:</Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>{parsedResume.email || 'N/A'}</Typography>
              
              <Typography variant="subtitle1">Phone:</Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>{parsedResume.phone || 'N/A'}</Typography>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle1">Skills:</Typography>
              <Box sx={{ mb: 2 }}>
                {parsedResume.skills && parsedResume.skills.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {parsedResume.skills.map((skill, index) => (
                      <Chip key={index} label={skill} color="primary" variant="outlined" />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body1">No skills found</Typography>
                )}
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1">Experience:</Typography>
              {parsedResume.experience && parsedResume.experience.length > 0 ? (
                <List dense>
                  {parsedResume.experience.map((exp, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={typeof exp === 'object' ? `${exp.title} at ${exp.company}` : exp}
                        secondary={typeof exp === 'object' ? `${exp.dates}: ${exp.description}` : ''}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body1" sx={{ mb: 2 }}>No experience found</Typography>
              )}
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1">Education:</Typography>
              {parsedResume.education && parsedResume.education.length > 0 ? (
                <List dense>
                  {parsedResume.education.map((edu, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={typeof edu === 'object' ? `${edu.degree} from ${edu.institution}` : edu}
                        secondary={typeof edu === 'object' ? edu.dates : ''}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body1">No education found</Typography>
              )}
            </Grid>
          </Grid>
        </Paper>
      )}
      
      {resumeHistory.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Resume History
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Grid container spacing={2}>
            {resumeHistory.map((item, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {item.resume.name || 'Unnamed Resume'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      ID: {item.resume_id}
                    </Typography>
                    <Typography variant="body2">
                      Skills: {item.resume.skills ? item.resume.skills.slice(0, 3).join(', ') : 'None'} 
                      {item.resume.skills && item.resume.skills.length > 3 ? '...' : ''}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button size="small" onClick={() => setParsedResume(item.resume)}>
                      View Details
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

export default ResumePage;
