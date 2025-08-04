import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const HomePage = ({ onSelect }) => {
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        setConnected(localStorage.getItem('gsc_connected') === 'true');
    }, []);

    const handleConnect = () => {
        const clientId = import.meta.env.VITE_GSC_CLIENT_ID;
        const redirectUri = import.meta.env.VITE_GSC_REDIRECT_URI;
        const state = crypto.randomUUID();
        sessionStorage.setItem('gsc_oauth_state', state);
        const scope = encodeURIComponent('https://www.googleapis.com/auth/webmasters.readonly');
        const authUrl =
            `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}` +
            `&redirect_uri=${encodeURIComponent(redirectUri)}` +
            `&response_type=code&scope=${scope}&access_type=offline&prompt=consent&state=${state}`;
        window.location.href = authUrl;
    };

    return (
        <div className="flex flex-col justify-top items-center h-screen p-12">
            <h1 className="text-4xl font-bold mb-12 text-primary-content">What are we making today?</h1>
            <div
                className="card w-[400px] h-[150px] bg-gradient-to-r from-accent to-primary text-gray-800 shadow-lg mb-4 cursor-pointer transform transition-transform hover:scale-105 hover:shadow-yellow-500/50"
                onClick={() => onSelect('generate')}
            >
                <div className="card-body">
                    <h2 className="card-title text-2xl font-bold">Generate a New Article</h2>
                    <p className="text-lg">Create a new article from scratch.</p>
                </div>
            </div>
            <div
                className="card w-[400px] h-[150px] bg-gradient-to-r from-accent to-secondary text-gray-800 shadow-lg cursor-pointer transform transition-transform hover:scale-105 hover:shadow-teal-300/50"
                onClick={() => onSelect('optimize')}
            >
                <div className="card-body">
                    <h2 className="card-title text-2xl font-bold">Optimize Existing Content</h2>
                    <p className="text-lg">Enhance and analyze your existing content.</p>
                </div>
            </div>
            <div
                className={`card w-[400px] h-[150px] bg-gradient-to-r from-accent to-neutral text-gray-800 shadow-lg mt-4 ${connected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer transform transition-transform hover:scale-105 hover:shadow-neutral-300/50'}`}
                onClick={() => {
                    if (!connected) handleConnect();
                }}
            >
                <div className="card-body">
                    <h2 className="card-title text-2xl font-bold">{connected ? 'Google Search Console Connected' : 'Connect Google Search Console'}</h2>
                    <p className="text-lg">{connected ? 'Your account is linked.' : 'Link your account to import data.'}</p>
                </div>
            </div>
        </div>
    );
};
HomePage.propTypes = {
    onSelect: PropTypes.func.isRequired,
};

export default HomePage;

