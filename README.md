# Online Auction System

## Description
An online auction platform where buyers can request sellers to list items for auction. The system supports features such as user registration, bidding, item management, and transaction handling.

## Features
- **User registration**: Buyers and sellers can create accounts.
- **Auction creation**: Sellers can list items for auction.
- **Bidding**: Buyers can place bids on items they are interested in.
- **Transaction history**: View the transaction details for each auction.
- **Feedback system**: Buyers and sellers can leave feedback after an auction.

## Installation and Setup

### Prerequisites
- Python 3.x
- Flask
- SQLite (or another database depending on your setup)

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Yashwanthvm06/Online-Auction-System.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Online-Auction-System
   ```
3. Install the necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask application:
   ```bash
   python app.py
   ```
The application will start, and you can access it at http://localhost:5000.

## Project Structure

The project is organized as follows:

```
Online-Auction-System/
│
├── app.py                 # Main application entry point
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # HTML templates for the application
│   ├── add_auction.html
│   ├── auction_history.html
│   ├── auction-detail.html
│   ├── base.html
│   ├── bidding_page.html
│   ├── buyer_request.html
│   ├── dashboard.html
│   ├── edit_auction.html
│   ├── feedback_payment.html
│   ├── index.html
│   ├── login.html
│   ├── match_requests.html
│   ├── payment_confirmation.html
│   ├── register.html
│   ├── respond_to_request.html
│   ├── seller.html
│   ├── transaction_history.html
│   ├── update_auction.html
│   └── view_requests.html
└── database/              # Database files
    └── auction.db         # SQLite database file
```

This structure separates concerns, making the project easier to maintain and scale.

