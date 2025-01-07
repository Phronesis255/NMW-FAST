// src/App.jsx
import React, { useState, useRef } from 'react';
import HomePage from './components/HomePage';
import SearchForm from './components/SearchForm';
import GenerateArticle from './components/GenerateArticle';
import AnalysisResults from './components/AnalysisResults';
import EditorComponent from './components/EditorComponent';
import Loading from './components/Loading';
import SeoScale from './components/SeoScale';
import axios from 'axios';

const App = () => {
    const [page, setPage] = useState('home');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showEditor, setShowEditor] = useState(false);
    const [showSeoScale, setShowSeoScale] = useState(false);
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

    const handleSelect = (selection) => {
        setPage(selection);
    };

    return (
        <div>
            {page === 'home' && <HomePage onSelect={handleSelect} />}
            {page === 'generate' && <GenerateArticle />}
            {page === 'optimize' && (
                <>
                    <SearchForm onSearch={handleSearch} />
                    {loading && <Loading />}
                    {error && <div>Error: {error}</div>}
                    {results && <AnalysisResults results={results} />}
                    {showEditor && <EditorComponent content={editorContent.current} />}
                    {showSeoScale && <SeoScale />}
                </>
            )}
        </div>
    );
};

export default App;