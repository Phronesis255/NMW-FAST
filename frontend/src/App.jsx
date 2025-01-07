// src/App.jsx
import React, { useState, useRef } from 'react';
import SearchForm from './components/SearchForm';
import AnalysisResults from './components/AnalysisResults';
import EditorComponent from './components/EditorComponent';
import Loading from './components/Loading';
import SeoScale from './components/SeoScale';
import DrawerSidebar from './components/DrawerSidebar';
import axios from 'axios';
import { Button } from '@mui/material';

// Calculate term metrics ...
const calculateTermMetrics = (tfidfTerms, targetScores, wordCount) => {
    return tfidfTerms.map((term) => {
        const avgTfScore = targetScores[term] || 0;
        const target = avgTfScore; // directly use tf_score
        const delta = Math.max(1, Math.floor(target * 0.1));
        const minOccurrences = Math.max(1, target - delta);
        const maxOccurrences = target + delta;
        return { term, target, delta, minOccurrences, maxOccurrences };
    });
};

const App = () => {
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showEditor, setShowEditor] = useState(false);
    const [showSeoScale, setShowSeoScale] = useState(false);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const editorContent = useRef("");

    const handleSearch = async (keyword) => {
        setLoading(true);
        setError(null);
        setResults(null);
        setShowEditor(false);
        setShowSeoScale(false);
        try {
            console.log("[DEBUG] Fetching analysis results...");
            const response = await axios.post('http://localhost:8000/api/analyze', { keyword });
            setResults(response.data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const toggleDrawer = (open) => (event) => {
        if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
            return;
        }
        setDrawerOpen(open);
    };

    return (
        <div>
            <SearchForm onSearch={handleSearch} />
            <Button variant="contained" color="primary" onClick={toggleDrawer(true)}>
                Generate a New Article
            </Button>
            <DrawerSidebar open={drawerOpen} onClose={toggleDrawer(false)} />
            {loading && <Loading />}
            {error && <div>Error: {error}</div>}
            {results && <AnalysisResults results={results} />}
            {showEditor && <EditorComponent content={editorContent.current} />}
            {showSeoScale && <SeoScale />}
        </div>
    );
};

export default App;