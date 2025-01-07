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
        <div className="container mx-auto p-6">
            <h1 className="text-3xl font-bold mb-6 text-left">Start optimizing your content</h1>

            {/* If showing SEO @ SCALE screen */}
            {showSeoScale && (
                <SeoScale onBack={handleBackFromSeoScale} />
            )}

            {showGenerateArticle && (
                <GenerateArticle onBack={handleBackFromGenerateArticle} />
            )}

            {/* If not showing SEO @ SCALE and not showing editor */}
            {!showSeoScale && !showGenerateArticle && !showEditor && (
                <>
                    <SearchForm onSearch={handleSearch} onSeoScale={handleSeoScale} />
                    <button
                        onClick={handleGenerateArticle}
                        className="btn btn-accent mt-6"
                    >
                        Generate a New Article
                    </button>
                    {loading && <Loading />}
                    {error && <div className="text-red-500 mt-4">Error: {error}</div>}
                    {results && (
                        <>
                            <AnalysisResults results={results} />
                            <button
                                onClick={toggleEditor}
                                className="btn btn-primary mt-6"
                            >
                                Go to Editor
                            </button>
                        </>
                    )}
                </>
            )}

            {/* If showing editor */}
            {!showSeoScale && !showGenerateArticle && showEditor && (
                <>
                    <EditorComponent
                        tfidfTerms={tfidfTerms}
                        targetScores={targetScores}
                        onChange={handleEditorChange}
                    />
                    <div className="flex justify-between mt-6">
                        <button
                            onClick={toggleEditor}
                            className="btn btn-secondary"
                        >
                            Back to Analysis
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default App;