// src/App.jsx
import React, { useState, useRef } from 'react';
import SearchForm from './components/SearchForm';
import AnalysisResults from './components/AnalysisResults';
import EditorComponent from './components/EditorComponent';
import Loading from './components/Loading';
import SeoScale from './components/SeoScale';
import axios from 'axios';

// ------------------------------------------
// Calculate term metrics (unchanged from old)
// ------------------------------------------
const calculateTermMetrics = (tfidfTerms, targetScores, wordCount) => {
    return tfidfTerms.map((term) => {
        const avgTfScore = targetScores[term] || 0;
        // Directly use the tf_score as the "target"
        const target = avgTfScore;

        // +/-10% around the target
        const delta = Math.max(1, Math.floor(target * 0.1));
        const minOccurrences = Math.max(1, target - delta);
        const maxOccurrences = target + delta;

        return {
            term,
            target,
            delta,
            minOccurrences,
            maxOccurrences
        };
    });
};

const App = () => {
    // ------------------
    // State and Refs
    // ------------------
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Toggles for Editor and SEO @ Scale screens
    const [showEditor, setShowEditor] = useState(false);
    const [showSeoScale, setShowSeoScale] = useState(false);

    // Ref to hold the editor content
    const editorContent = useRef("");

    // --------------------------------------
    // 1) Handle Search
    // --------------------------------------
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
            console.log("[DEBUG] Results fetched successfully:", response.data);
        } catch (err) {
            console.error("[DEBUG] API Error:", err);
            setError(err.message || "An error occurred during the analysis.");
        } finally {
            setLoading(false);
        }
    };

    // --------------------------------------
    // 2) Editor change + toggles
    // --------------------------------------
    const handleEditorChange = (data) => {
        editorContent.current = data;
        console.log("[DEBUG] Updated editor content:", data);
    };

    const toggleEditor = () => {
        setShowEditor(!showEditor);
    };

    // --------------------------------------
    // 3) SEO @ Scale toggles
    // --------------------------------------
    const handleSeoScale = () => {
        // Show the SEO @ Scale screen
        setShowSeoScale(true);
        setShowEditor(false);
    };

    const handleBackFromSeoScale = () => {
        // Hide SEO @ Scale screen
        setShowSeoScale(false);
    };

    // --------------------------------------
    // 4) Term metric calculations
    // --------------------------------------
    const tfidfTerms = results?.tfidf_terms?.map((termObj) => termObj.word) || [];
    const targetScores = results?.tfidf_terms?.reduce((acc, termObj) => {
        acc[termObj.word] = termObj.tf_score || 0;
        return acc;
    }, {}) || {};

    // Count words in Editor
    const wordCount = editorContent.current.split(/\s+/).filter(Boolean).length || 1;
    // Calculate term metrics
    const termsMetrics = calculateTermMetrics(tfidfTerms, targetScores, wordCount);
    console.log("[DEBUG] Calculated Term Metrics:", termsMetrics);

    // --------------------------------------
    // 5) Render
    // --------------------------------------
    return (
        <div className="container mx-auto p-6">
            <h1 className="text-3xl font-bold mb-6 text-left">Start optimizing your content</h1>

            {/* If showing SEO @ SCALE screen */}
            {showSeoScale && (
                <SeoScale onBack={handleBackFromSeoScale} />
            )}

            {/* If NOT showing SEO @ SCALE and NOT showing editor */}
            {!showSeoScale && !showEditor && (
                <>
                    <SearchForm onSearch={handleSearch} onSeoScale={handleSeoScale} />
                    {loading && <Loading />}
                    {error && <div className="text-red-500 mt-4">Error: {error}</div>}

                    {results && (
                        <>
                            <AnalysisResults results={results} />
                            
                            {/* Button to toggle Editor */}
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

            {/* If showing editor (and not showing SEO @ SCALE) */}
            {!showSeoScale && showEditor && (
                <>
                    <EditorComponent
                        // Pass data to Editor
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
