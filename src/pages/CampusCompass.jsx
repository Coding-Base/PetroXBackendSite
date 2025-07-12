// src/components/CampusCompass.jsx
import React, { useState, useEffect, useRef } from 'react';
import { GoogleMap, LoadScript, Marker, DirectionsRenderer, InfoWindow } from '@react-google-maps/api';

// Set Google Maps API key (replace with your actual key)
const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

const containerStyle = {
  width: '100%',
  height: '70vh'
};

const universities = [
  {
    id: 'futo',
    name: 'Federal University of Technology Owerri (FUTO)',
    location: { lat: 5.3875, lng: 7.0353 },
    locations: [
      {
        id: 'lecture-hall-1',
        name: 'Lecture Hall Complex 1',
        position: { lat: 5.3890, lng: 7.0360 },
        category: 'Lecture Halls',
        description: 'Main lecture halls for engineering departments',
        hours: 'Mon-Fri: 8am-6pm, Sat: 9am-1pm',
        popularTimes: ['8-10am: Busy', '1-3pm: Moderate', '4-6pm: Busy'],
        floorPlan: 'https://example.com/futo/lecture-hall-1-floorplan.jpg'
      },
      {
        id: 'lecture-hall-2',
        name: 'Lecture Hall Complex 2',
        position: { lat: 5.3882, lng: 7.0375 },
        category: 'Lecture Halls',
        description: 'Lecture halls for science departments',
        hours: 'Mon-Fri: 8am-6pm',
        popularTimes: ['9-11am: Very Busy', '2-4pm: Moderate'],
        floorPlan: 'https://example.com/futo/lecture-hall-2-floorplan.jpg'
      },
      {
        id: 'senate',
        name: 'Senate Building',
        position: { lat: 5.3862, lng: 7.0338 },
        category: 'Administration',
        description: 'University administration offices',
        hours: 'Mon-Fri: 8am-4pm',
        popularTimes: ['10am-12pm: Busy', '2-3pm: Moderate']
      },
      {
        id: 'ict',
        name: 'ICT Center',
        position: { lat: 5.3881, lng: 7.0345 },
        category: 'Services',
        description: 'Information and Communication Technology center',
        hours: 'Mon-Fri: 8am-6pm, Sat: 9am-2pm',
        popularTimes: ['9-11am: Very Busy', '3-5pm: Busy']
      },
      {
        id: 'library',
        name: 'University Library',
        position: { lat: 5.3878, lng: 7.0372 },
        category: 'Academic',
        description: 'Main academic library with over 50,000 volumes',
        hours: 'Mon-Fri: 8am-8pm, Sat: 9am-4pm',
        popularTimes: ['10am-12pm: Very Busy', '4-6pm: Busy']
      },
      {
        id: 'cafeteria',
        name: 'Main Cafeteria',
        position: { lat: 5.3865, lng: 7.0358 },
        category: 'Services',
        description: 'Main student dining hall',
        hours: 'Daily: 7am-8pm',
        popularTimes: ['12-1pm: Very Busy', '5-6pm: Busy']
      },
      {
        id: 'sports-complex',
        name: 'Sports Complex',
        position: { lat: 5.3901, lng: 7.0327 },
        category: 'Recreation',
        description: 'University sports facilities',
        hours: 'Mon-Sat: 6am-8pm',
        popularTimes: ['4-6pm: Very Busy']
      }
    ]
  },
  {
    id: 'unilag',
    name: 'University of Lagos',
    location: { lat: 6.5244, lng: 3.3792 },
    locations: [
      {
        id: 'main-auditorium',
        name: 'J.F. Ade-Ajayi Auditorium',
        position: { lat: 6.5240, lng: 3.3785 },
        category: 'Lecture Halls',
        description: 'Main university auditorium',
        hours: 'Mon-Fri: 8am-6pm'
      }
    ]
  },
  {
    id: 'ui',
    name: 'University of Ibadan',
    location: { lat: 7.4459, lng: 3.8969 },
    locations: []
  }
];

export default function CampusCompass() {
  const [selectedUniversity, setSelectedUniversity] = useState('futo');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [directions, setDirections] = useState(null);
  const [userPosition, setUserPosition] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [locations, setLocations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [favorites, setFavorites] = useState([]);
  const [showAddLocation, setShowAddLocation] = useState(false);
  const [newLocation, setNewLocation] = useState({
    name: '',
    category: '',
    description: '',
    hours: '',
    floorPlan: ''
  });
  const [map, setMap] = useState(null);
  const mapRef = useRef(null);
  
  // Get user location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserPosition({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.error("Error getting location:", error);
          // Default to FUTO position if location access denied
          setUserPosition({ lat: 5.3875, lng: 7.0353 });
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    } else {
      // Default to FUTO position if geolocation not supported
      setUserPosition({ lat: 5.3875, lng: 7.0353 });
    }
  }, []);

  // Load favorites from localStorage
  useEffect(() => {
    const savedFavorites = localStorage.getItem('campusCompassFavorites');
    if (savedFavorites) {
      setFavorites(JSON.parse(savedFavorites));
    }
  }, []);

  // Save favorites to localStorage
  useEffect(() => {
    localStorage.setItem('campusCompassFavorites', JSON.stringify(favorites));
  }, [favorites]);

  // Update categories when university changes
  useEffect(() => {
    if (selectedUniversity) {
      const uni = universities.find(u => u.id === selectedUniversity);
      const uniqueCategories = [...new Set(uni.locations.map(loc => loc.category))];
      setCategories(uniqueCategories);
      setLocations(uni.locations);
      setSelectedCategory('');
      setSelectedLocation(null);
      setSearchQuery('');
    }
  }, [selectedUniversity]);

  // Filter locations by category
  useEffect(() => {
    if (selectedUniversity && selectedCategory) {
      const uni = universities.find(u => u.id === selectedUniversity);
      setLocations(uni.locations.filter(loc => 
        loc.category === selectedCategory
      ));
    }
  }, [selectedCategory, selectedUniversity]);

  // Filter locations by search query
  useEffect(() => {
    if (selectedUniversity && searchQuery) {
      const uni = universities.find(u => u.id === selectedUniversity);
      const filtered = uni.locations.filter(loc => 
        loc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        loc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        loc.category.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setLocations(filtered);
    }
  }, [searchQuery, selectedUniversity]);

  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
    
    if (userPosition) {
      setIsLoading(true);
      
      const directionsService = new window.google.maps.DirectionsService();
      directionsService.route(
        {
          origin: userPosition,
          destination: location.position,
          travelMode: window.google.maps.TravelMode.WALKING
        },
        (result, status) => {
          if (status === window.google.maps.DirectionsStatus.OK) {
            setDirections(result);
          } else {
            console.error(`Directions request failed: ${status}`);
          }
          setIsLoading(false);
        }
      );
    }
  };

  const toggleFavorite = (locationId) => {
    if (favorites.includes(locationId)) {
      setFavorites(favorites.filter(id => id !== locationId));
    } else {
      setFavorites([...favorites, locationId]);
    }
  };

  const handleAddLocation = () => {
    if (!newLocation.name || !newLocation.category) return;
    
    const newLoc = {
      ...newLocation,
      id: `custom-${Date.now()}`,
      position: map.getCenter(),
      popularTimes: [],
      addedBy: "User"
    };
    
    const updatedLocations = [...locations, newLoc];
    setLocations(updatedLocations);
    
    // Update the university locations (in a real app, this would be sent to a server)
    const uniIndex = universities.findIndex(u => u.id === selectedUniversity);
    if (uniIndex !== -1) {
      universities[uniIndex].locations = updatedLocations;
    }
    
    setNewLocation({
      name: '',
      category: '',
      description: '',
      hours: '',
      floorPlan: ''
    });
    setShowAddLocation(false);
  };

  const handleMapClick = () => {
    if (showAddLocation) {
      setShowAddLocation(false);
    }
  };

  const getCenter = () => {
    if (selectedUniversity) {
      return universities.find(u => u.id === selectedUniversity).location;
    }
    return { lat: 5.3875, lng: 7.0353 }; // Default to FUTO
  };

  return (
    <div className="flex flex-col h-screen p-4 md:p-6 bg-gray-50">
      <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Campus Compass</h1>
      <p className="text-gray-600 mb-4">Navigate your campus with ease</p>
      
      <div className="flex flex-col md:flex-row gap-4 mb-4">
        <div className="w-full md:w-1/3">
          <label className="block text-sm font-medium mb-1">Select University</label>
          <select
            value={selectedUniversity}
            onChange={(e) => setSelectedUniversity(e.target.value)}
            className="w-full p-2 border rounded bg-white"
          >
            {universities.map(uni => (
              <option key={uni.id} value={uni.id}>{uni.name}</option>
            ))}
          </select>
        </div>
        
        <div className="w-full md:w-1/3">
          <label className="block text-sm font-medium mb-1">Category</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full p-2 border rounded bg-white"
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
        
        <div className="w-full md:w-1/3">
          <label className="block text-sm font-medium mb-1">Search Locations</label>
          <div className="relative">
            <input
              type="text"
              placeholder="Search by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full p-2 border rounded pl-10 bg-white"
            />
            <svg 
              className="absolute left-3 top-2.5 text-gray-400 w-5 h-5" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
        </div>
      </div>
      
      <div className="flex flex-col md:flex-row flex-1 gap-4">
        <div className="w-full md:w-1/3 bg-white rounded-lg shadow-md p-4 overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">
              {selectedCategory ? `${selectedCategory} (${locations.length})` : 'All Locations'}
            </h2>
            <button 
              className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
              onClick={() => setShowAddLocation(!showAddLocation)}
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              Add Location
            </button>
          </div>
          
          {showAddLocation && (
            <div className="mb-4 p-3 border rounded bg-blue-50">
              <h3 className="font-medium mb-2">Add New Location</h3>
              <input
                type="text"
                placeholder="Location Name"
                value={newLocation.name}
                onChange={(e) => setNewLocation({...newLocation, name: e.target.value})}
                className="w-full p-2 mb-2 border rounded"
              />
              <select
                value={newLocation.category}
                onChange={(e) => setNewLocation({...newLocation, category: e.target.value})}
                className="w-full p-2 mb-2 border rounded"
              >
                <option value="">Select Category</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <textarea
                placeholder="Description"
                value={newLocation.description}
                onChange={(e) => setNewLocation({...newLocation, description: e.target.value})}
                className="w-full p-2 mb-2 border rounded"
                rows="2"
              />
              <div className="flex gap-2">
                <button 
                  className="flex-1 bg-blue-600 text-white py-1 px-3 rounded hover:bg-blue-700"
                  onClick={handleAddLocation}
                >
                  Add
                </button>
                <button 
                  className="flex-1 bg-gray-200 py-1 px-3 rounded hover:bg-gray-300"
                  onClick={() => setShowAddLocation(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          
          <div className="mb-4">
            <button 
              className={`text-sm px-3 py-1 rounded mr-2 ${favorites.length > 0 ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'}`}
              onClick={() => {
                if (favorites.length > 0) {
                  const favLocations = locations.filter(loc => favorites.includes(loc.id));
                  setLocations(favLocations);
                }
              }}
            >
              Favorites ({favorites.length})
            </button>
            <button 
              className="text-sm bg-gray-100 px-3 py-1 rounded hover:bg-gray-200"
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory('');
                const uni = universities.find(u => u.id === selectedUniversity);
                setLocations(uni.locations);
              }}
            >
              Reset Filters
            </button>
          </div>
          
          {locations.length > 0 ? (
            <div className="space-y-3">
              {locations.map(location => (
                <div 
                  key={location.id}
                  className={`p-3 border rounded cursor-pointer hover:bg-blue-50 relative ${
                    selectedLocation?.id === location.id ? 'bg-blue-100 border-blue-500' : ''
                  }`}
                  onClick={() => handleLocationSelect(location)}
                >
                  <button 
                    className="absolute top-3 right-3 text-amber-400 hover:text-amber-600"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFavorite(location.id);
                    }}
                  >
                    {favorites.includes(location.id) ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                      </svg>
                    )}
                  </button>
                  
                  <h3 className="font-medium">{location.name}</h3>
                  <p className="text-sm text-gray-600">{location.description}</p>
                  
                  <div className="flex flex-wrap gap-1 mt-2">
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {location.category}
                    </span>
                    {location.hours && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        {location.hours.split(',')[0]}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              {searchQuery ? 'No locations match your search' : 'No locations found in this category'}
            </p>
          )}
        </div>
        
        <div className="w-full md:w-2/3 bg-white rounded-lg shadow-md overflow-hidden">
          <LoadScript googleMapsApiKey={GOOGLE_MAPS_API_KEY}>
            <GoogleMap
              mapContainerStyle={containerStyle}
              center={getCenter()}
              zoom={16}
              options={{
                streetViewControl: false,
                mapTypeControl: false,
                fullscreenControl: false,
                styles: [
                  {
                    featureType: "poi",
                    elementType: "labels",
                    stylers: [{ visibility: "off" }]
                  }
                ]
              }}
              onLoad={map => {
                mapRef.current = map;
                setMap(map);
              }}
              onClick={handleMapClick}
            >
              {/* User Location Marker */}
              {userPosition && (
                <Marker 
                  position={userPosition}
                  icon={{
                    path: window.google.maps.SymbolPath.CIRCLE,
                    scale: 8,
                    fillColor: "#4285F4",
                    fillOpacity: 1,
                    strokeColor: "#FFFFFF",
                    strokeWeight: 2
                  }}
                >
                  <InfoWindow>
                    <div className="p-2">
                      <h3 className="font-bold">Your Location</h3>
                      <p className="text-sm">You are here</p>
                    </div>
                  </InfoWindow>
                </Marker>
              )}
              
              {/* University Locations */}
              {locations.map(location => (
                <Marker
                  key={location.id}
                  position={location.position}
                  onClick={() => handleLocationSelect(location)}
                  icon={{
                    url: `https://maps.google.com/mapfiles/ms/icons/${
                      location.category === 'Lecture Halls' ? 'blue' : 
                      location.category === 'Administration' ? 'red' : 
                      location.category === 'Services' ? 'green' : 'orange'
                    }-dot.png`,
                    scaledSize: new window.google.maps.Size(32, 32)
                  }}
                />
              ))}
              
              {/* Selected Location Info */}
              {selectedLocation && (
                <InfoWindow
                  position={selectedLocation.position}
                  onCloseClick={() => setSelectedLocation(null)}
                >
                  <div className="p-2 max-w-xs">
                    <h3 className="font-bold text-lg">{selectedLocation.name}</h3>
                    <p className="text-gray-700 mb-2">{selectedLocation.description}</p>
                    
                    <div className="mb-2">
                      <p className="font-medium">Hours:</p>
                      <p className="text-sm">{selectedLocation.hours || 'Not specified'}</p>
                    </div>
                    
                    {selectedLocation.popularTimes && (
                      <div className="mb-2">
                        <p className="font-medium">Popular Times:</p>
                        <div className="space-y-1 mt-1">
                          {selectedLocation.popularTimes.map((time, i) => (
                            <div key={i} className="flex items-center">
                              <div className={`w-3 h-3 rounded-full mr-2 ${
                                time.includes('Busy') ? 'bg-red-500' : 
                                time.includes('Moderate') ? 'bg-yellow-500' : 'bg-green-500'
                              }`}></div>
                              <span className="text-sm">{time}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {selectedLocation.floorPlan && (
                      <div className="mb-2">
                        <p className="font-medium">Floor Plan:</p>
                        <a 
                          href={selectedLocation.floorPlan} 
                          target="_blank" 
                          rel="noreferrer"
                          className="text-blue-600 text-sm hover:underline"
                        >
                          View Indoor Map
                        </a>
                      </div>
                    )}
                    
                    {selectedLocation.addedBy && (
                      <p className="text-xs text-gray-500 mt-2">
                        Added by: {selectedLocation.addedBy}
                      </p>
                    )}
                    
                    <button 
                      className="mt-2 text-blue-600 hover:underline text-sm"
                      onClick={() => handleLocationSelect(selectedLocation)}
                    >
                      Get Directions
                    </button>
                  </div>
                </InfoWindow>
              )}
              
              {/* Directions */}
              {directions && (
                <DirectionsRenderer directions={directions} />
              )}
            </GoogleMap>
          </LoadScript>
          
          <div className="p-4 border-t">
            <h3 className="font-medium mb-2">Legend:</h3>
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center">
                <div className="w-4 h-4 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-sm">Lecture Halls</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-red-500 rounded-full mr-2"></div>
                <span className="text-sm">Administration</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
                <span className="text-sm">Services</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-orange-500 rounded-full mr-2"></div>
                <span className="text-sm">Other</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg flex items-center">
            <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500 mr-3"></div>
            <p className="text-lg">Calculating directions...</p>
          </div>
        </div>
      )}
    </div>
  );
}