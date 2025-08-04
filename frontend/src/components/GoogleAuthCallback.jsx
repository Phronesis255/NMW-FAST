import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const GoogleAuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    const storedState = sessionStorage.getItem('gsc_oauth_state');

    if (code && state && state === storedState) {
      // Remove OAuth params from the URL
      window.history.replaceState({}, document.title, window.location.pathname);
      sessionStorage.removeItem('gsc_oauth_state');

      axios
        .post('http://localhost:8000/api/google-auth', { code })
        .then(() => {
          localStorage.setItem('gsc_connected', 'true');
          navigate('/');
        })
        .catch((err) => {
          console.error('Google OAuth error', err);
          navigate('/');
        });
    } else {
      navigate('/');
    }
  }, [navigate]);

  return <p className="p-12">Connecting to Google Search Console...</p>;
};

export default GoogleAuthCallback;
