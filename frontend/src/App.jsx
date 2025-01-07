// src/App.jsx
import React, { useState, useRef } from 'react';
import SearchForm from './components/SearchForm';
import AnalysisResults from './components/AnalysisResults';
import EditorComponent from './components/EditorComponent';
import Loading from './components/Loading';
import SeoScale from './components/SeoScale';
import GenerateArticle from './components/GenerateArticle';
import axios from 'axios';

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
    const [showGenerateArticle, setShowGenerateArticle] = useState(false);
    const editorContent = useRef("");

    const handleSearch = async (keyword) => {
        setLoading(true);
        setError(null);
        setResults(null);
        setShowEditor(false);
        setShowSeoScale(false);
        setShowGenerateArticle(false);
        try {
            console.log("[DEBUG] Fetching analysis results...");
            const response = await axios.post('http://localhost:8000/api/analyze', { keyword });
            setResults(response.data);
            console.log("[DEBUG] Results fetched successfully:", response.data);
        } catch (err) {
            console.error("[DEBUG] API Error:", err);
            setError(err.message || "An error occurred during the analysis.");
        } finally {
            setLoading(false);
        }
    };

    const handleEditorChange = (data) => {
        editorContent.current = data;
        console.log("[DEBUG] Updated editor content:", data);
    };

    const toggleEditor = () => {
        setShowEditor(!showEditor);
    };

    const handleSeoScale = () => {
        // Show the SEO @ SCALE screen
        setShowSeoScale(true);
        setShowEditor(false);
        setShowGenerateArticle(false);
    };

    const handleBackFromSeoScale = () => {
        // Return to the main screen (hide SEO @ SCALE)
        setShowSeoScale(false);
    };

    const handleGenerateArticle = () => {
        setShowGenerateArticle(true);
        setShowSeoScale(false);
        setShowEditor(false);
    };

    const handleBackFromGenerateArticle = () => {
        setShowGenerateArticle(false);
    };

    const tfidfTerms = results?.tfidf_terms?.map((termObj) => termObj.word) || [];
    const targetScores = results?.tfidf_terms?.reduce((acc, termObj) => {
        acc[termObj.word] = termObj.tf_score || 0;
        return acc;
    }, {}) || {};

    const wordCount = editorContent.current.split(/\s+/).filter(Boolean).length || 1;
    const termsMetrics = calculateTermMetrics(tfidfTerms, targetScores, wordCount);

    console.log("[DEBUG] Calculated Term Metrics:", termsMetrics);

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
                        className="btn btn-primary mt-6"
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
