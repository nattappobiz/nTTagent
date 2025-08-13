# ElderDocs Frontend

This is the React frontend for the ElderDocs document management system.

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm (comes with Node.js)

### Installation

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

### Environment Variables

Create a `.env` file in this directory to configure the API endpoint:

```
REACT_APP_API_URL=http://localhost:8000
```

During development, the app loads this value automatically. If the variable is
absent, it falls back to `http://localhost:8000`.

For production or other environments, set `REACT_APP_API_URL` before running a
build. Example scripts are provided:

```
npm run build:staging
npm run build:prod
```

### Running the Application

1. Start the development server:
   ```
   npm start
   ```

2. Open your browser and visit `http://localhost:3000`

### Building for Production

To create a production build:
```
npm run build:prod
```

## Project Structure

```
frontend/
├── public/              # Static files
├── src/                 # React source code
│   ├── components/      # React components
│   ├── services/        # API service layer
│   ├── App.js           # Main App component
│   ├── App.css          # App-specific styles
│   ├── index.js         # Entry point
│   └── index.css        # Global styles
├── package.json         # Project dependencies and scripts
└── README.md            # This file
```

## Features

- View citizen records in a table format
- Upload PDF documents containing citizen information
- Communicates with the backend API specified by `REACT_APP_API_URL`

## API Endpoints

The frontend communicates with the following backend endpoints:

- `GET /files` - Get all citizens
- `POST /uploads` - Upload PDF documents
- `GET /files?status={status}` - Get citizens filtered by status
- `PUT /citizens/{id}` - Update a specific citizen
- `GET /export` - Export data

## Development

The frontend is built with:
- React.js
- Axios for HTTP requests
- CSS for styling

To modify the application, edit the files in the `src/` directory.

## Available Scripts

In the project directory, you can run:

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).