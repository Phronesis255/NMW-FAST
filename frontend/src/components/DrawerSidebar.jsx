// src/components/DrawerSidebar.jsx
import React from 'react';
import { Drawer, Button, Box } from '@mui/material';
import GenerateArticle from './GenerateArticle';

const DrawerSidebar = ({ open, onClose }) => {
    return (
        <Drawer anchor="right" open={open} onClose={onClose}>
            <Box
                sx={{ width: 250 }}
                role="presentation"
                onClick={onClose}
                onKeyDown={onClose}
            >
                <GenerateArticle />
            </Box>
        </Drawer>
    );
};

export default DrawerSidebar;
// This component is a simple drawer sidebar that contains a GenerateArticle component. The GenerateArticle component will be used to generate an article based on the analysis results. The drawer sidebar is opened and closed using the open and onClose props passed to it.