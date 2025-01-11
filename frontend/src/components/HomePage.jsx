import React from 'react';

const HomePage = ({ onSelect }) => {
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
        </div>
    );
};

export default HomePage;