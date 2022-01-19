# hotelContentRanking
Python Plotly dashboard showing chain &amp; hotel level content scores.
We parsed various propeties descriptive content to find if it lists following facilities/attributes.
<details>
  <summary>Click to expand!</summary>
  
  ## Hotel Attributes
  1. HotelCode
  2. HotelName
  3. Services
  4. AcceptedPayments
  5. PolicyInfo
  6. CheckInTime
  7. CheckOutTime
  8. PenaltyDescription
  9. TaxPolicies
  10. RefPoint
  11. Phone
  12. Dinning
  13. MeetingRooms
  14. SegmentCategory
  15. CommissionPolicy
  16. LanguageSpoken
  
  ## Room Attributes
  1. RoomTypeCode
  2. RoomType_Name
  3. Quantity
  4. Image_url
  5. BedTypeCode
  6. RoomClassificationCode
  7. RoomCategory
  8. Amenity
  9. MaxOccupancy
  10. MaxAdultOccupancy
  11. MaxChildOccupancy
  12. Room_Description
  13. Score
  14. ChainCode
  15. ChainName
</details>

The score per property is based on listed Hotel & Room attributes.
Total score for a chain is average of property score.

# dependency
Python 3.x
- pandas
- dash
- dash_bootstrap_components
- dash_core_components
- dash_html_components
- plotly

`scr` folder has both the app (py script) & `pandas` pickled data.

# screenshot
## Main Screen
It lists total hotels & chain.
Show the chain attribute score & total number of listed properties under them
![Main Screen](screenshots/page1.jpg)
## Hotel Chain Screen
Plots list of properties wrt attribute score.
Drop down menu shows top 15 propeties
![Screen 2](screenshots/page2.jpg)
## Property Screen
Proerty page list Property level & room level attributes.
![Screen 3](screenshots/page3.jpg)
