// API Base URL
const API_URL = 'http://localhost:5000/api';

// Global state
let selectedSlot = null;
let allSlots = [];
let userBookings = [];

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return false;
    }
    return token;
}

// Get headers with auth token
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    };
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Show section
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.dashboard-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active from all menu items
    document.querySelectorAll('.sidebar-menu li').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionId).classList.add('active');
    
    // Add active to clicked menu item
    const clickedItem = document.querySelector(`a[href="#${sectionId}"]`).parentElement;
    clickedItem.classList.add('active');
    
    // Load section data
    switch(sectionId) {
        case 'overview':
            loadOverview();
            break;
        case 'book':
            loadAvailableSlots();
            break;
        case 'bookings':
            loadBookings();
            break;
        case 'profile':
            loadProfile();
            break;
    }
}

// Load overview data
async function loadOverview() {
    try {
        // Load slots
        const slotsResponse = await fetch(`${API_URL}/slots`, {
            headers: getHeaders()
        });
        const slotsData = await slotsResponse.json();
        
        const totalSlots = slotsData.length;
        const availableSlots = slotsData.filter(s => s.status === 'available').length;
        
        document.getElementById('totalSlots').textContent = totalSlots;
        document.getElementById('availableSlots').textContent = availableSlots;
        
        // Load bookings
        const bookingsResponse = await fetch(`${API_URL}/bookings/my`, {
            headers: getHeaders()
        });
        const bookingsData = await bookingsResponse.json();
        
        const activeBookings = bookingsData.filter(b => b.status === 'active').length;
        let totalSpent = 0;
        bookingsData.forEach(b => {
            if (b.total_amount) totalSpent += b.total_amount;
        });
        
        document.getElementById('activeBookings').textContent = activeBookings;
        document.getElementById('totalSpent').textContent = `₹${totalSpent}`;
        
    } catch (error) {
        console.error('Error loading overview:', error);
    }
}

// Load available slots
async function loadAvailableSlots() {
    try {
        const response = await fetch(`${API_URL}/slots`, {
            headers: getHeaders()
        });
        
        if (response.ok) {
            allSlots = await response.json();
            displaySlots(allSlots);
        }
    } catch (error) {
        console.error('Error loading slots:', error);
        document.getElementById('slotsList').innerHTML = '<p class="loading">Error loading slots</p>';
    }
}

// Display slots
function displaySlots(slots) {
    const slotsList = document.getElementById('slotsList');
    
    const availableSlots = slots.filter(s => s.status === 'available');
    
    if (availableSlots.length === 0) {
        slotsList.innerHTML = '<p class="loading">No available slots</p>';
        return;
    }
    
    slotsList.innerHTML = availableSlots.map(slot => `
        <div class="slot-item ${slot.status}" onclick="selectSlot('${slot._id}', '${slot.slot_number}', ${slot.hourly_rate}, '${slot.type}')">
            <div class="slot-number">${slot.slot_number}</div>
            <div class="slot-type">${slot.type}</div>
            <div class="slot-type">₹${slot.hourly_rate}/hr</div>
        </div>
    `).join('');
}

// Filter slots by type
function filterSlots() {
    const slotType = document.getElementById('slotType').value;
    
    let filtered = allSlots;
    if (slotType !== 'all') {
        filtered = allSlots.filter(s => s.type === slotType && s.status === 'available');
    } else {
        filtered = allSlots.filter(s => s.status === 'available');
    }
    
    displaySlots(filtered);
}

// Select slot
function selectSlot(slotId, slotNumber, hourlyRate, slotType) {
    // Remove previous selection
    document.querySelectorAll('.slot-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked slot
    event.target.closest('.slot-item').classList.add('selected');
    
    selectedSlot = {
        id: slotId,
        number: slotNumber,
        rate: hourlyRate,
        type: slotType
    };
    
    updateBookingSummary();
    document.getElementById('bookButton').disabled = false;
}

// Update booking summary
function updateBookingSummary() {
    const duration = parseInt(document.getElementById('duration').value) || 0;
    
    if (selectedSlot) {
        document.getElementById('selectedSlotDisplay').textContent = `${selectedSlot.number} (${selectedSlot.type})`;
    } else {
        document.getElementById('selectedSlotDisplay').textContent = 'None';
    }
    
    document.getElementById('durationDisplay').textContent = `${duration} hour${duration !== 1 ? 's' : ''}`;
    
    const totalAmount = selectedSlot ? selectedSlot.rate * duration : 0;
    document.getElementById('totalAmount').textContent = `₹${totalAmount}`;
}

// Handle booking form submission
document.addEventListener('DOMContentLoaded', function() {
    const token = checkAuth();
    if (!token) return;
    
    // Load user data
    const user = JSON.parse(localStorage.getItem('user'));
    document.getElementById('userName').textContent = user.full_name || user.email;
    
    // Load initial overview
    loadOverview();
    
    // Duration change handler
    const durationInput = document.getElementById('duration');
    if (durationInput) {
        durationInput.addEventListener('input', updateBookingSummary);
    }
    
    // Booking form handler
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!selectedSlot) {
                alert('Please select a parking slot');
                return;
            }
            
            const duration = parseInt(document.getElementById('duration').value);
            
            try {
                const response = await fetch(`${API_URL}/bookings`, {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({
                        slot_id: selectedSlot.id,
                        duration_hours: duration
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Booking successful!');
                    selectedSlot = null;
                    bookingForm.reset();
                    showSection('bookings');
                } else {
                    alert(data.message || 'Booking failed');
                }
            } catch (error) {
                console.error('Booking error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }
    
    // Profile form handler
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const profileData = {
                full_name: document.getElementById('profileName').value,
                phone: document.getElementById('profilePhone').value,
                vehicle_number: document.getElementById('profileVehicle').value
            };
            
            try {
                const response = await fetch(`${API_URL}/users/profile`, {
                    method: 'PUT',
                    headers: getHeaders(),
                    body: JSON.stringify(profileData)
                });
                
                if (response.ok) {
                    const updatedUser = await response.json();
                    localStorage.setItem('user', JSON.stringify(updatedUser));
                    alert('Profile updated successfully!');
                } else {
                    alert('Failed to update profile');
                }
            } catch (error) {
                console.error('Profile update error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }
});

// Load bookings
async function loadBookings(filter = 'all') {
    try {
        const response = await fetch(`${API_URL}/bookings/my`, {
            headers: getHeaders()
        });
        
        if (response.ok) {
            userBookings = await response.json();
            displayBookings(userBookings, filter);
        }
    } catch (error) {
        console.error('Error loading bookings:', error);
        document.getElementById('bookingsList').innerHTML = '<p class="loading">Error loading bookings</p>';
    }
}

// Display bookings
function displayBookings(bookings, filter) {
    const bookingsList = document.getElementById('bookingsList');
    
    let filteredBookings = bookings;
    if (filter !== 'all') {
        filteredBookings = bookings.filter(b => b.status === filter);
    }
    
    if (filteredBookings.length === 0) {
        bookingsList.innerHTML = '<p class="loading">No bookings found</p>';
        return;
    }
    
    bookingsList.innerHTML = filteredBookings.map(booking => {
        const startDate = new Date(booking.start_time).toLocaleString();
        const endDate = booking.end_time ? new Date(booking.end_time).toLocaleString() : 'N/A';
        
        return `
            <div class="booking-card">
                <div class="booking-icon">
                    <i class="fas fa-parking"></i>
                </div>
                <div class="booking-info">
                    <h4>Slot ${booking.slot_number || booking.slot_id}</h4>
                    <div class="booking-details">
                        <span><i class="fas fa-clock"></i> ${startDate}</span>
                        <span><i class="fas fa-hourglass"></i> ${booking.duration_hours || 0}h</span>
                        <span><i class="fas fa-rupee-sign"></i> ₹${booking.total_amount || 0}</span>
                    </div>
                </div>
                <div class="booking-actions">
                    <span class="badge ${booking.status}">${booking.status}</span>
                    ${booking.status === 'active' ? `
                        <button class="btn btn-sm btn-outline" onclick="cancelBooking('${booking._id}')">
                            Cancel
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Filter bookings
function filterBookings(filter) {
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    displayBookings(userBookings, filter);
}

// Cancel booking
async function cancelBooking(bookingId) {
    if (!confirm('Are you sure you want to cancel this booking?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/bookings/${bookingId}/cancel`, {
            method: 'PUT',
            headers: getHeaders()
        });
        
        if (response.ok) {
            alert('Booking cancelled successfully');
            loadBookings();
        } else {
            alert('Failed to cancel booking');
        }
    } catch (error) {
        console.error('Cancel booking error:', error);
        alert('An error occurred. Please try again.');
    }
}

// Load profile
function loadProfile() {
    const user = JSON.parse(localStorage.getItem('user'));
    
    document.getElementById('profileName').value = user.full_name || '';
    document.getElementById('profileEmail').value = user.email || '';
    document.getElementById('profilePhone').value = user.phone || '';
    document.getElementById('profileVehicle').value = user.vehicle_number || '';
}
