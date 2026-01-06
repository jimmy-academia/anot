# Request Reference (philly_cafes)

Complete reference for all 80 benchmark requests.


## G01


### R00: Busy Parent
**Gold**: [0] Milkcrate Cafe

**Text**: Looking for a cafe that's kid-friendly, with a drive-thru, and without TVs

**Shorthand**: `AND(drive_thru, good_for_kids, no_tv)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "drive_thru",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DriveThru"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "good_for_kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "no_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "False"
      }
    }
  ]
}
```

### R01: Special Occasion
**Gold**: [1] Tria Cafe Rittenhouse

**Text**: Looking for a cafe that's upscale, with bike parking, and with free WiFi

**Shorthand**: `AND(upscale, bike_parking, wifi_free)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "upscale",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "3"
      }
    },
    {
      "aspect": "bike_parking",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BikeParking"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "wifi_free",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'free'"
      }
    }
  ]
}
```

### R02: Winter Night Out
**Gold**: [2] Front Street Cafe

**Text**: Looking for a cafe with coat check, with a full bar, and with a hipster vibe

**Shorthand**: `AND(coat_check, full_bar, hipster_vibe)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "coat_check",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "CoatCheck"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "full_bar",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'full_bar'"
      }
    },
    {
      "aspect": "hipster_vibe",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'hipster': True"
      }
    }
  ]
}
```

### R03: Teen Hangout
**Gold**: [4] Kung Fu Tea

**Text**: Looking for a cafe that's lively, kid-friendly, with TVs, and indoor-only

**Shorthand**: `AND(lively, indoor, has_tv, good_for_kids)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "lively",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'loud'"
      }
    },
    {
      "aspect": "indoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "has_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "good_for_kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R04: Focused Work
**Gold**: [7] Swiss Haus Cafe & Pastry Bar

**Text**: Looking for a cafe that's quiet, indoor-only, no reservations needed, and good for groups

**Shorthand**: `AND(quiet, indoor, no_reservations, good_for_groups)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'quiet'"
      }
    },
    {
      "aspect": "indoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "no_reservations",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsReservations"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "good_for_groups",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsGoodForGroups"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R05: Dog Owner Writer
**Gold**: [13] Steap and Grind

**Text**: Looking for a cafe that's dog-friendly, quiet, good for groups

**Shorthand**: `AND(dog_friendly, quiet, good_for_groups)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "dog_friendly",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'quiet'"
      }
    },
    {
      "aspect": "good_for_groups",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsGoodForGroups"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R06: Birthday Brunch
**Gold**: [5] Function Coffee Labs

**Text**: Looking for a cafe that's BYOB, trendy, with bike parking

**Shorthand**: `AND(byob, trendy, bike_parking)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "trendy",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'trendy': True"
      }
    },
    {
      "aspect": "bike_parking",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BikeParking"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R07: Digital Detox
**Gold**: [14] La Colombe Coffee

**Text**: Looking for a cafe without WiFi, indoor-only, and not aimed at kids

**Shorthand**: `AND(no_wifi, indoor, not_for_kids)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "no_wifi",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'no'"
      }
    },
    {
      "aspect": "indoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "not_for_kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "False"
      }
    }
  ]
}
```

### R08: Rainy Dog Walk
**Gold**: [18] Chapterhouse Café & Gallery

**Text**: Looking for a cafe that's dog-friendly, budget-friendly, kid-friendly, with takeout, and indoor-only

**Shorthand**: `AND(dog_friendly, indoor, price_cheap, good_for_kids, takeout)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "dog_friendly",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "indoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "price_cheap",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "1"
      }
    },
    {
      "aspect": "good_for_kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "takeout",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R09: Instagram Influencer
**Gold**: [16] Elixr Coffee Roasters

**Text**: Looking for a cafe that's quiet, trendy, budget-friendly

**Shorthand**: `AND(quiet, trendy, price_cheap)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'quiet'"
      }
    },
    {
      "aspect": "trendy",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'trendy': True"
      }
    },
    {
      "aspect": "price_cheap",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "1"
      }
    }
  ]
}
```

## G02


### R10: Music Lover
**Gold**: [3] MilkBoy

**Text**: Looking for a cafe with a casual atmosphere, has reviews mentioning 'live music', no reservations needed, and without WiFi

**Shorthand**: `AND(live_music, casual_vibe, no_reservations, wifi_none)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "live_music",
      "evidence": {
        "kind": "review_text",
        "pattern": "live music"
      }
    },
    {
      "aspect": "casual_vibe",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'casual': True"
      }
    },
    {
      "aspect": "no_reservations",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsReservations"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "wifi_none",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'no'"
      }
    }
  ]
}
```

### R11: Dessert Lover
**Gold**: [9] Gran Caffe L'Aquila

**Text**: Looking for a cafe that's mid-priced, with takeout, has reviews mentioning 'gelato', and good for lunch

**Shorthand**: `AND(gelato, price_mid, lunch, takeout)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "gelato",
      "evidence": {
        "kind": "review_text",
        "pattern": "gelato"
      }
    },
    {
      "aspect": "price_mid",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "2"
      }
    },
    {
      "aspect": "lunch",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForMeal"
        ],
        "contains": "'lunch': True"
      }
    },
    {
      "aspect": "takeout",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R12: Wine Enthusiast
**Gold**: [1] Tria Cafe Rittenhouse

**Text**: Looking for a cafe with takeout, has reviews mentioning 'wine bar', offers delivery, and takes reservations

**Shorthand**: `AND(wine_bar, delivery, takeout, reservations)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "wine_bar",
      "evidence": {
        "kind": "review_text",
        "pattern": "wine bar"
      }
    },
    {
      "aspect": "delivery",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsDelivery"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "takeout",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "reservations",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsReservations"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R13: Brunch Connoisseur
**Gold**: [19] Sabrina's Café

**Text**: Looking for a cafe with free WiFi, has reviews mentioning 'challah', good for breakfast, without TVs, and offers delivery

**Shorthand**: `AND(wifi_free, challah, breakfast, no_tv, delivery)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "wifi_free",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'free'"
      }
    },
    {
      "aspect": "challah",
      "evidence": {
        "kind": "review_text",
        "pattern": "challah"
      }
    },
    {
      "aspect": "breakfast",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForMeal"
        ],
        "contains": "'breakfast': True"
      }
    },
    {
      "aspect": "no_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "delivery",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsDelivery"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R14: Dog Parent
**Gold**: [13] Steap and Grind

**Text**: Looking for a cafe with TVs, with takeout, with a casual atmosphere, has reviews mentioning 'dog friendly', and accepts credit cards

**Shorthand**: `AND(dog_friendly_reviews, has_tv, takeout, casual_vibe, credit_cards)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "dog_friendly_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "dog friendly"
      }
    },
    {
      "aspect": "has_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "takeout",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "casual_vibe",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'casual': True"
      }
    },
    {
      "aspect": "credit_cards",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BusinessAcceptsCreditCards"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R15: Matcha Addict
**Gold**: [17] United By Blue

**Text**: Looking for a cafe that's mid-priced, has reviews mentioning 'matcha latte', and without TVs

**Shorthand**: `AND(matcha_latte, price_mid, no_tv)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "matcha_latte",
      "evidence": {
        "kind": "review_text",
        "pattern": "matcha latte"
      }
    },
    {
      "aspect": "price_mid",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "2"
      }
    },
    {
      "aspect": "no_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "False"
      }
    }
  ]
}
```

### R16: Night Owl
**Gold**: [10] Thirsty Dice

**Text**: Looking for a cafe that's kid-friendly, wheelchair accessible, with free WiFi, has reviews mentioning 'midnight', and takes reservations

**Shorthand**: `AND(midnight, wifi_free, good_for_kids, reservations, wheelchair)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "midnight",
      "evidence": {
        "kind": "review_text",
        "pattern": "midnight"
      }
    },
    {
      "aspect": "wifi_free",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'free'"
      }
    },
    {
      "aspect": "good_for_kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "reservations",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsReservations"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "wheelchair",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WheelchairAccessible"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R17: Foodie
**Gold**: [2] Front Street Cafe

**Text**: Looking for a cafe with coat check, mid-priced, with bike parking, has reviews mentioning 'banh mi', and good for brunch

**Shorthand**: `AND(coat_check, banh_mi, brunch, price_mid, bike_parking)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "coat_check",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "CoatCheck"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "banh_mi",
      "evidence": {
        "kind": "review_text",
        "pattern": "banh mi"
      }
    },
    {
      "aspect": "brunch",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForMeal"
        ],
        "contains": "'brunch': True"
      }
    },
    {
      "aspect": "price_mid",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "2"
      }
    },
    {
      "aspect": "bike_parking",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BikeParking"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R18: Fresh Air
**Gold**: [2] Front Street Cafe

**Text**: Looking for a cafe with free WiFi, with a casual atmosphere, has reviews mentioning 'terrace', and good for breakfast

**Shorthand**: `AND(terrace, wifi_free, casual_vibe, breakfast)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "terrace",
      "evidence": {
        "kind": "review_text",
        "pattern": "terrace"
      }
    },
    {
      "aspect": "wifi_free",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'free'"
      }
    },
    {
      "aspect": "casual_vibe",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'casual': True"
      }
    },
    {
      "aspect": "breakfast",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForMeal"
        ],
        "contains": "'breakfast': True"
      }
    }
  ]
}
```

### R19: Pet Owner
**Gold**: [18] Chapterhouse Café & Gallery

**Text**: Looking for a cafe that's budget-friendly, has reviews mentioning 'bring your dog', and accepts credit cards

**Shorthand**: `AND(bring_dog, price_cheap, credit_cards)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "bring_dog",
      "evidence": {
        "kind": "review_text",
        "pattern": "bring your dog"
      }
    },
    {
      "aspect": "price_cheap",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "1"
      }
    },
    {
      "aspect": "credit_cards",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BusinessAcceptsCreditCards"
        ],
        "true": "True"
      }
    }
  ]
}
```

## G03


### R20: Early Bird Workspace
**Gold**: [16] Elixr Coffee Roasters

**Text**: Looking for a cafe that's quiet, budget-friendly, not kid-friendly, with bike parking, and open on Monday from 7:00 AM to 8:00 AM

**Shorthand**: `AND(monday_early, quiet, not_for_kids, bike_parking, price_cheap)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "monday_early",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Monday"
        ],
        "true": "7:0-8:0"
      }
    },
    {
      "aspect": "quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'quiet'"
      }
    },
    {
      "aspect": "not_for_kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "bike_parking",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BikeParking"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "price_cheap",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "1"
      }
    }
  ]
}
```

### R21: Friday Wine Evening
**Gold**: [1] Tria Cafe Rittenhouse

**Text**: Looking for a cafe with beer and wine, open on Friday from 6:00 PM to 9:00 PM, and without TVs

**Shorthand**: `AND(friday_evening, beer_wine, no_tv)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "friday_evening",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Friday"
        ],
        "true": "18:0-21:0"
      }
    },
    {
      "aspect": "beer_wine",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "'beer_and_wine'"
      }
    },
    {
      "aspect": "no_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "False"
      }
    }
  ]
}
```

### R22: Sunday Dog Walk
**Gold**: [13] Steap and Grind

**Text**: Looking for a cafe that's dog-friendly, quiet, with takeout, and open on Sunday from 8:00 AM to 10:00 AM

**Shorthand**: `AND(sunday_morning, dogs, quiet, takeout)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "sunday_morning",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Sunday"
        ],
        "true": "8:0-10:0"
      }
    },
    {
      "aspect": "dogs",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'quiet'"
      }
    },
    {
      "aspect": "takeout",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R23: Monday Afternoon Party
**Gold**: [3] MilkBoy

**Text**: Looking for a cafe that's lively, with a full bar, with casual dress code, and open on Monday from 2:00 PM to 4:00 PM

**Shorthand**: `AND(monday_afternoon, full_bar, loud, casual_attire)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "monday_afternoon",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Monday"
        ],
        "true": "14:0-16:0"
      }
    },
    {
      "aspect": "full_bar",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'full_bar'"
      }
    },
    {
      "aspect": "loud",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'loud'"
      }
    },
    {
      "aspect": "casual_attire",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsAttire"
        ],
        "true": "u'casual'"
      }
    }
  ]
}
```

### R24: Early Friday Dog Brunch
**Gold**: [17] United By Blue

**Text**: Looking for a cafe that's dog-friendly, with outdoor seating, with a casual atmosphere, open on Friday from 7:00 AM to 9:00 AM, and accepts credit cards

**Shorthand**: `AND(friday_early, dogs, outdoor, casual_vibe, credit_cards)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "friday_early",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Friday"
        ],
        "true": "7:0-9:0"
      }
    },
    {
      "aspect": "dogs",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "outdoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "casual_vibe",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'casual': True"
      }
    },
    {
      "aspect": "credit_cards",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BusinessAcceptsCreditCards"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R25: Late Night Loud
**Gold**: [3] MilkBoy

**Text**: Looking for a cafe that's lively, open on Friday from 10:00 PM to 1:00 AM, and without WiFi

**Shorthand**: `AND(friday_late, loud, no_wifi)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "friday_late",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Friday"
        ],
        "true": "22:0-1:0"
      }
    },
    {
      "aspect": "loud",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'loud'"
      }
    },
    {
      "aspect": "no_wifi",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'no'"
      }
    }
  ]
}
```

### R26: Midweek Dog Lunch
**Gold**: [13] Steap and Grind

**Text**: Looking for a cafe that's dog-friendly, quiet, with outdoor seating, and open on Wednesday from 12:00 PM to 2:00 PM

**Shorthand**: `AND(wednesday_lunch, dogs, outdoor, quiet)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "wednesday_lunch",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Wednesday"
        ],
        "true": "12:0-14:0"
      }
    },
    {
      "aspect": "dogs",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "outdoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'quiet'"
      }
    }
  ]
}
```

### R27: Friday Night Bar Patio
**Gold**: [9] Gran Caffe L'Aquila

**Text**: Looking for a cafe with a full bar, with outdoor seating, with moderate noise, open on Friday from 9:00 PM to 11:00 PM, and takes reservations

**Shorthand**: `AND(friday_late, full_bar, outdoor, average_noise, reservations)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "friday_late",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Friday"
        ],
        "true": "21:0-23:0"
      }
    },
    {
      "aspect": "full_bar",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'full_bar'"
      }
    },
    {
      "aspect": "outdoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "average_noise",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'average'"
      }
    },
    {
      "aspect": "reservations",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsReservations"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R28: Sunday Family Bar Happy Hour
**Gold**: [9] Gran Caffe L'Aquila

**Text**: Looking for a cafe that's kid-friendly, with a full bar, with outdoor seating, with happy hour, and open on Sunday from 12:00 PM to 5:00 PM

**Shorthand**: `AND(sunday_afternoon, full_bar, kids, outdoor, happy_hour)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "sunday_afternoon",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Sunday"
        ],
        "true": "12:0-17:0"
      }
    },
    {
      "aspect": "full_bar",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'full_bar'"
      }
    },
    {
      "aspect": "kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "outdoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "happy_hour",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HappyHour"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R29: Indoor Family Bar Sunday
**Gold**: [10] Thirsty Dice

**Text**: Looking for a cafe that's kid-friendly, with a full bar, open on Sunday from 12:00 PM to 5:00 PM, and without outdoor seating

**Shorthand**: `AND(sunday_afternoon, full_bar, kids, no_outdoor)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "sunday_afternoon",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Sunday"
        ],
        "true": "12:0-17:0"
      }
    },
    {
      "aspect": "full_bar",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'full_bar'"
      }
    },
    {
      "aspect": "kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "no_outdoor",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "not_true": "True"
      }
    }
  ]
}
```

## G04


### R30: Expert Coffee Recommendation
**Gold**: [0] Milkcrate Cafe

**Text**: Looking for a cafe with a drive-thru, hipster vibe, has experienced reviewers mentioning 'coffee', and no dogs allowed

**Shorthand**: `AND(drive_thru, hipster, no_dogs, coffee_by_experts)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "drive_thru",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DriveThru"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "hipster",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'hipster': True"
      }
    },
    {
      "aspect": "no_dogs",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "not_true": "True"
      }
    },
    {
      "aspect": "coffee_by_experts",
      "evidence": {
        "kind": "review_text",
        "pattern": "coffee",
        "weight_by": {
          "field": [
            "user",
            "review_count"
          ]
        }
      }
    }
  ]
}
```

### R31: Influencer Workspace
**Gold**: [3] MilkBoy

**Text**: Looking for a cafe that's lively, not aimed at kids, with a casual atmosphere, has popular reviewers mentioning 'work', and without WiFi

**Shorthand**: `AND(loud, no_wifi, work_by_influencers, casual_vibe, not_for_kids)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "loud",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'loud'"
      }
    },
    {
      "aspect": "no_wifi",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'no'"
      }
    },
    {
      "aspect": "work_by_influencers",
      "evidence": {
        "kind": "review_text",
        "pattern": "work",
        "weight_by": {
          "field": [
            "user",
            "fans"
          ]
        }
      }
    },
    {
      "aspect": "casual_vibe",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'casual': True"
      }
    },
    {
      "aspect": "not_for_kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "False"
      }
    }
  ]
}
```

### R32: Elite Love No Coat Check
**Gold**: [9] Gran Caffe L'Aquila

**Text**: Looking for a cafe with a full bar, has elite reviewers mentioning 'love', without coat check, and offers delivery, and good for dinner

**Shorthand**: `AND(full_bar, no_coat_check, love_by_elite, delivery, dinner)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "full_bar",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'full_bar'"
      }
    },
    {
      "aspect": "no_coat_check",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "CoatCheck"
        ],
        "not_true": "True"
      }
    },
    {
      "aspect": "love_by_elite",
      "evidence": {
        "kind": "review_text",
        "pattern": "love",
        "weight_by": {
          "field": [
            "user",
            "elite"
          ]
        }
      }
    },
    {
      "aspect": "delivery",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsDelivery"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "dinner",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForMeal"
        ],
        "contains": "'dinner': True"
      }
    }
  ]
}
```

### R33: Hidden Gem by Trusted Reviewers
**Gold**: [12] Hinge Cafe

**Text**: Looking for a cafe that's BYOB, with casual dress code, with takeout, where helpful reviews mention 'hidden gem', and accepts credit cards

**Shorthand**: `AND(byob, hidden_gem_trusted, casual_attire, credit_cards, takeout)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "hidden_gem_trusted",
      "evidence": {
        "kind": "review_text",
        "pattern": "hidden gem",
        "weight_by": {
          "field": [
            "useful"
          ]
        }
      }
    },
    {
      "aspect": "casual_attire",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsAttire"
        ],
        "true": "u'casual'"
      }
    },
    {
      "aspect": "credit_cards",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BusinessAcceptsCreditCards"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "takeout",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R34: Elite Bubble Tea Crowd
**Gold**: [4] Kung Fu Tea

**Text**: Looking for a cafe that's lively, budget-friendly, with bike parking, with TVs, and has elite reviewers mentioning 'bubble'

**Shorthand**: `AND(loud, bubble_by_elite, bike_parking, has_tv, price_cheap)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "loud",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'loud'"
      }
    },
    {
      "aspect": "bubble_by_elite",
      "evidence": {
        "kind": "review_text",
        "pattern": "bubble",
        "weight_by": {
          "field": [
            "user",
            "elite"
          ]
        }
      }
    },
    {
      "aspect": "bike_parking",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BikeParking"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "has_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "price_cheap",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "1"
      }
    }
  ]
}
```

### R35: Trendy Quiet Workspace
**Gold**: [16] Elixr Coffee Roasters

**Text**: Looking for a cafe that's quiet, trendy, with free WiFi, and has experienced reviewers mentioning 'work'

**Shorthand**: `AND(quiet, trendy, work_by_pros, wifi_free)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'quiet'"
      }
    },
    {
      "aspect": "trendy",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'trendy': True"
      }
    },
    {
      "aspect": "work_by_pros",
      "evidence": {
        "kind": "review_text",
        "pattern": "work",
        "weight_by": {
          "field": [
            "user",
            "review_count"
          ]
        }
      }
    },
    {
      "aspect": "wifi_free",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "true": "u'free'"
      }
    }
  ]
}
```

### R36: Quiet Beer Wine Spot
**Gold**: [7] Swiss Haus Cafe & Pastry Bar

**Text**: Looking for a cafe that's quiet, with beer and wine, and has experienced reviewers mentioning 'work'

**Shorthand**: `AND(quiet, beer_wine, work_by_pros)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "true": "u'quiet'"
      }
    },
    {
      "aspect": "beer_wine",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'beer_and_wine'"
      }
    },
    {
      "aspect": "work_by_pros",
      "evidence": {
        "kind": "review_text",
        "pattern": "work",
        "weight_by": {
          "field": [
            "user",
            "review_count"
          ]
        }
      }
    }
  ]
}
```

### R37: Family Game Night Elite
**Gold**: [10] Thirsty Dice

**Text**: Looking for a cafe that's kid-friendly, wheelchair accessible, with a full bar, has elite reviewers mentioning 'game', and takes reservations

**Shorthand**: `AND(full_bar, kids, game_by_elite, reservations, wheelchair)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "full_bar",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'full_bar'"
      }
    },
    {
      "aspect": "kids",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "game_by_elite",
      "evidence": {
        "kind": "review_text",
        "pattern": "game",
        "weight_by": {
          "field": [
            "user",
            "elite"
          ]
        }
      }
    },
    {
      "aspect": "reservations",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsReservations"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "wheelchair",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WheelchairAccessible"
        ],
        "true": "True"
      }
    }
  ]
}
```

### R38: Elite Brunch BYOB
**Gold**: [11] Cafe La Maude

**Text**: Looking for a cafe that's BYOB, with a classy atmosphere, has elite reviewers mentioning 'brunch', and good for breakfast

**Shorthand**: `AND(byob, brunch_by_elite, classy_vibe, breakfast)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "brunch_by_elite",
      "evidence": {
        "kind": "review_text",
        "pattern": "brunch",
        "weight_by": {
          "field": [
            "user",
            "elite"
          ]
        }
      }
    },
    {
      "aspect": "classy_vibe",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'classy': True"
      }
    },
    {
      "aspect": "breakfast",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForMeal"
        ],
        "contains": "'breakfast': True"
      }
    }
  ]
}
```

### R39: Hipster Brunch Bar
**Gold**: [2] Front Street Cafe

**Text**: Looking for a cafe with a hipster vibe, with a full bar, has experienced reviewers mentioning 'brunch', and good for lunch

**Shorthand**: `AND(hipster, full_bar, brunch_by_experts, lunch)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "hipster",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'hipster': True"
      }
    },
    {
      "aspect": "full_bar",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "true": "u'full_bar'"
      }
    },
    {
      "aspect": "brunch_by_experts",
      "evidence": {
        "kind": "review_text",
        "pattern": "brunch",
        "weight_by": {
          "field": [
            "user",
            "review_count"
          ]
        }
      }
    },
    {
      "aspect": "lunch",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForMeal"
        ],
        "contains": "'lunch': True"
      }
    }
  ]
}
```

## G05


### R40: Upscale Wine Night
**Gold**: [0] Milkcrate Cafe

**Text**: Looking for a cafe with a drive-thru that either has reviews mentioning 'love' or has reviews mentioning 'breakfast' or has popular reviewers mentioning 'best' or has elite reviewers mentioning 'love'

**Shorthand**: `AND(drive_thru, OR(love_reviews, breakfast_reviews, review_meta_reviewer_popularity_best, review_meta_elite_status_love))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "drive_thru",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DriveThru"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "love_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "love"
          }
        },
        {
          "aspect": "breakfast_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "breakfast"
          }
        },
        {
          "aspect": "review_meta_reviewer_popularity_best",
          "evidence": {
            "kind": "review_text",
            "pattern": "best",
            "weight_by": {
              "field": [
                "user",
                "fans"
              ]
            }
          }
        },
        {
          "aspect": "review_meta_elite_status_love",
          "evidence": {
            "kind": "review_text",
            "pattern": "love",
            "weight_by": {
              "field": [
                "user",
                "elite"
              ]
            }
          }
        }
      ]
    }
  ]
}
```

### R41: Family Game Night
**Gold**: [1] Tria Cafe Rittenhouse

**Text**: Looking for a cafe that's upscale that either has reviews mentioning 'cozy' or has elite reviewers mentioning 'love' or has elite reviewers mentioning 'recommend' or has reviews mentioning 'latte'

**Shorthand**: `AND(price_upscale, OR(cozy, review_meta_elite_status_love, review_meta_elite_status_recommend, latte_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "price_upscale",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "3"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "cozy",
          "evidence": {
            "kind": "review_text",
            "pattern": "cozy"
          }
        },
        {
          "aspect": "review_meta_elite_status_love",
          "evidence": {
            "kind": "review_text",
            "pattern": "love",
            "weight_by": {
              "field": [
                "user",
                "elite"
              ]
            }
          }
        },
        {
          "aspect": "review_meta_elite_status_recommend",
          "evidence": {
            "kind": "review_text",
            "pattern": "recommend",
            "weight_by": {
              "field": [
                "user",
                "elite"
              ]
            }
          }
        },
        {
          "aspect": "latte_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "latte"
          }
        }
      ]
    }
  ]
}
```

### R42: Teen Boba Party
**Gold**: [21] K'Far Cafe

**Text**: Looking for a cafe that's intimate that either has popular reviewers mentioning 'love' or has reviews mentioning 'favorite' or has reviews mentioning 'art' or has reviews mentioning 'cocktail'

**Shorthand**: `AND(ambience_intimate, OR(review_meta_reviewer_popularity_love, favorite_reviews, art_reviews, cocktail_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "ambience_intimate",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'intimate': True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "review_meta_reviewer_popularity_love",
          "evidence": {
            "kind": "review_text",
            "pattern": "love",
            "weight_by": {
              "field": [
                "user",
                "fans"
              ]
            }
          }
        },
        {
          "aspect": "favorite_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "favorite"
          }
        },
        {
          "aspect": "art_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "art"
          }
        },
        {
          "aspect": "cocktail_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "cocktail"
          }
        }
      ]
    }
  ]
}
```

### R43: Family Vietnamese Night
**Gold**: [25] Frieda

**Text**: Looking for a cafe with paid WiFi that either has reviews mentioning 'slow' or has experienced reviewers mentioning 'coffee' or has reviews mentioning 'brunch' or has reviews mentioning 'pastry'

**Shorthand**: `AND(wifi_paid, OR(slow_reviews, review_meta_reviewer_experience_coffee, brunch_reviews, pastry_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "wifi_paid",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "contains": "paid"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "slow_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "slow"
          }
        },
        {
          "aspect": "review_meta_reviewer_experience_coffee",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee",
            "weight_by": {
              "field": [
                "user",
                "review_count"
              ]
            }
          }
        },
        {
          "aspect": "brunch_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "brunch"
          }
        },
        {
          "aspect": "pastry_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "pastry|croissant|muffin"
          }
        }
      ]
    }
  ]
}
```

### R44: Hip Coat Check Bar
**Gold**: [32] Saxbys

**Text**: Looking for a cafe that's dine-in only that either has reviews mentioning 'fast' or has reviews mentioning 'latte' or has reviews mentioning 'friendly' or has elite reviewers mentioning 'work'

**Shorthand**: `AND(takeout_no, OR(fast_reviews, latte_reviews, friendly_reviews, review_meta_elite_status_work))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "takeout_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "fast_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "fast|quick"
          }
        },
        {
          "aspect": "latte_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "latte"
          }
        },
        {
          "aspect": "friendly_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "friendly"
          }
        },
        {
          "aspect": "review_meta_elite_status_work",
          "evidence": {
            "kind": "review_text",
            "pattern": "work",
            "weight_by": {
              "field": [
                "user",
                "elite"
              ]
            }
          }
        }
      ]
    }
  ]
}
```

### R45: Budget Dog Writer
**Gold**: [2] Front Street Cafe

**Text**: Looking for a cafe with a hipster vibe with coat check that either has reviews mentioning 'music' or has popular reviewers mentioning 'recommend' or has reviews mentioning 'meeting' or has reviews mentioning 'loud'

**Shorthand**: `AND(ambience_hipster, coat_check, OR(music_reviews, review_meta_reviewer_popularity_recommend, meeting_reviews, loud_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "ambience_hipster",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'hipster': True"
      }
    },
    {
      "aspect": "coat_check",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "CoatCheck"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "music_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "music"
          }
        },
        {
          "aspect": "review_meta_reviewer_popularity_recommend",
          "evidence": {
            "kind": "review_text",
            "pattern": "recommend",
            "weight_by": {
              "field": [
                "user",
                "fans"
              ]
            }
          }
        },
        {
          "aspect": "meeting_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "meeting"
          }
        },
        {
          "aspect": "loud_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "loud|noisy"
          }
        }
      ]
    }
  ]
}
```

### R46: Coffee Purist
**Gold**: [3] MilkBoy

**Text**: Looking for a cafe that's has reviews mentioning 'breakfast', adult-oriented that either has experienced reviewers mentioning 'work' or has reviews mentioning 'music' or has reviews mentioning 'love' or has reviews mentioning 'tea'

**Shorthand**: `AND(breakfast_reviews, kids_no, OR(review_meta_reviewer_experience_work, music_reviews, love_reviews, tea_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "breakfast_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "breakfast"
      }
    },
    {
      "aspect": "kids_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "review_meta_reviewer_experience_work",
          "evidence": {
            "kind": "review_text",
            "pattern": "work",
            "weight_by": {
              "field": [
                "user",
                "review_count"
              ]
            }
          }
        },
        {
          "aspect": "music_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "music"
          }
        },
        {
          "aspect": "love_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "love"
          }
        },
        {
          "aspect": "tea_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "tea"
          }
        }
      ]
    }
  ]
}
```

### R47: Trendy Dog Brunch
**Gold**: [4] Kung Fu Tea

**Text**: Looking for a cafe that's has reviews mentioning 'wine', lively that either has reviews mentioning 'book' or has reviews mentioning 'romantic' or has experienced reviewers mentioning 'love' or has reviews mentioning 'wifi'

**Shorthand**: `AND(wine_reviews, noise_loud, OR(books_reviews, romantic_reviews, review_meta_reviewer_experience_love, wifi_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "wine_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "wine"
      }
    },
    {
      "aspect": "noise_loud",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "contains": "loud"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "books_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "book"
          }
        },
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        },
        {
          "aspect": "review_meta_reviewer_experience_love",
          "evidence": {
            "kind": "review_text",
            "pattern": "love",
            "weight_by": {
              "field": [
                "user",
                "review_count"
              ]
            }
          }
        },
        {
          "aspect": "wifi_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "wifi|wi-fi"
          }
        }
      ]
    }
  ]
}
```

### R48: Indoor Tea Dog Walk
**Gold**: [5] Function Coffee Labs

**Text**: Looking for a cafe that's dog-friendly with a hipster vibe that either has elite reviewers mentioning 'coffee' or has experienced reviewers mentioning 'coffee' or has reviews mentioning 'recommend' or has elite reviewers mentioning 'work'

**Shorthand**: `AND(ambience_hipster, dogs_yes, OR(review_meta_elite_status_coffee, review_meta_reviewer_experience_coffee, recommend_reviews, review_meta_elite_status_work))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "ambience_hipster",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'hipster': True"
      }
    },
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "review_meta_elite_status_coffee",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee",
            "weight_by": {
              "field": [
                "user",
                "elite"
              ]
            }
          }
        },
        {
          "aspect": "review_meta_reviewer_experience_coffee",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee",
            "weight_by": {
              "field": [
                "user",
                "review_count"
              ]
            }
          }
        },
        {
          "aspect": "recommend_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "recommend"
          }
        },
        {
          "aspect": "review_meta_elite_status_work",
          "evidence": {
            "kind": "review_text",
            "pattern": "work",
            "weight_by": {
              "field": [
                "user",
                "elite"
              ]
            }
          }
        }
      ]
    }
  ]
}
```

### R49: Quiet Wine Brunch
**Gold**: [7] Swiss Haus Cafe & Pastry Bar

**Text**: Looking for a quiet cafe with beer and wine that either has reviews mentioning 'coffee' or has reviews mentioning 'pastry' or has reviews mentioning 'work' or has reviews mentioning 'friendly'

**Shorthand**: `AND(noise_quiet, alcohol_beer_wine, OR(coffee_reviews, pastry_reviews, work_reviews, friendly_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "noise_quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "contains": "quiet"
      }
    },
    {
      "aspect": "alcohol_beer_wine",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "contains": "beer_and_wine"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "coffee_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee"
          }
        },
        {
          "aspect": "pastry_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "pastry|croissant|muffin"
          }
        },
        {
          "aspect": "work_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "work|working|laptop"
          }
        },
        {
          "aspect": "friendly_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "friendly"
          }
        }
      ]
    }
  ]
}
```

## G06


### R50: Dine-In Date Night
**Gold**: [32] Saxbys

**Text**: Looking for a cafe with dine-in only (no takeout). Ideally known for romantic and coffee, or alternatively known for espresso and latte

**Shorthand**: `AND(takeout_no, OR(AND(romantic_reviews, coffee_reviews), AND(espresso_reviews, latte_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "takeout_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            },
            {
              "aspect": "coffee_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "espresso_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "espresso"
              }
            },
            {
              "aspect": "latte_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "latte"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R51: Paid WiFi Worker
**Gold**: [25] Frieda

**Text**: Looking for a cafe with paid WiFi. Ideally known for quiet and romantic, or alternatively known for coffee and latte

**Shorthand**: `AND(wifi_paid, OR(AND(quiet_reviews, romantic_reviews), AND(coffee_reviews, latte_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "wifi_paid",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "contains": "paid"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "quiet_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "quiet"
              }
            },
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "coffee_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee"
              }
            },
            {
              "aspect": "latte_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "latte"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R52: Intimate Brunch
**Gold**: [21] K'Far Cafe

**Text**: Looking for a cafe that's intimate. Ideally known for romantic and coffee, or alternatively known for espresso and latte

**Shorthand**: `AND(ambience_intimate, OR(AND(romantic_reviews, coffee_reviews), AND(espresso_reviews, latte_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "ambience_intimate",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'intimate': True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            },
            {
              "aspect": "coffee_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "espresso_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "espresso"
              }
            },
            {
              "aspect": "latte_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "latte"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R53: Dog-Friendly Indoor
**Gold**: [18] Chapterhouse Café & Gallery

**Text**: Looking for a cafe that's dog-friendly and indoor-only. Ideally known for cozy and quiet, or alternatively known for loud and romantic

**Shorthand**: `AND(dogs_yes, outdoor_no, OR(AND(cozy, quiet_reviews), AND(loud_reviews, romantic_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "outdoor_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "cozy",
              "evidence": {
                "kind": "review_text",
                "pattern": "cozy"
              }
            },
            {
              "aspect": "quiet_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "quiet"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "loud_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "loud|noisy"
              }
            },
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R54: BYOB Meeting Spot
**Gold**: [19] Sabrina's Café

**Text**: Looking for a cafe that's dog-friendly and known for meeting. Ideally known for cozy and quiet, or alternatively known for loud and coffee

**Shorthand**: `AND(dogs_yes, meeting_reviews, OR(AND(cozy, quiet_reviews), AND(loud_reviews, coffee_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "meeting_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "meeting"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "cozy",
              "evidence": {
                "kind": "review_text",
                "pattern": "cozy"
              }
            },
            {
              "aspect": "quiet_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "quiet"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "loud_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "loud|noisy"
              }
            },
            {
              "aspect": "coffee_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R55: Budget No-WiFi Focus
**Gold**: [14] La Colombe Coffee

**Text**: Looking for a cafe that's adult-oriented and indoor-only. Ideally known for cozy and quiet, or alternatively known for loud and romantic

**Shorthand**: `AND(kids_no, outdoor_no, OR(AND(cozy, quiet_reviews), AND(loud_reviews, romantic_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "kids_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "outdoor_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "cozy",
              "evidence": {
                "kind": "review_text",
                "pattern": "cozy"
              }
            },
            {
              "aspect": "quiet_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "quiet"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "loud_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "loud|noisy"
              }
            },
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R56: BYOB Music Lover
**Gold**: [12] Hinge Cafe

**Text**: Looking for a cafe that's BYOB and known for music. Ideally known for cozy and quiet, or alternatively known for romantic and coffee

**Shorthand**: `AND(byob, music_reviews, OR(AND(cozy, quiet_reviews), AND(romantic_reviews, coffee_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "music_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "music"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "cozy",
              "evidence": {
                "kind": "review_text",
                "pattern": "cozy"
              }
            },
            {
              "aspect": "quiet_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "quiet"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            },
            {
              "aspect": "coffee_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R57: Classy BYOB Brunch
**Gold**: [11] Cafe La Maude

**Text**: Looking for a cafe that's BYOB and classy. Ideally known for cozy and romantic, or alternatively known for coffee and latte

**Shorthand**: `AND(byob, ambience_classy, OR(AND(cozy, romantic_reviews), AND(coffee_reviews, latte_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "ambience_classy",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'classy': True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "cozy",
              "evidence": {
                "kind": "review_text",
                "pattern": "cozy"
              }
            },
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "coffee_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee"
              }
            },
            {
              "aspect": "latte_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "latte"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R58: Budget BYOB Coffee
**Gold**: [5] Function Coffee Labs

**Text**: Looking for a cafe that's budget-friendly and that's BYOB. Ideally known for cozy and romantic, or alternatively known for coffee and espresso

**Shorthand**: `AND(price_budget, byob, OR(AND(cozy, romantic_reviews), AND(coffee_reviews, espresso_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "price_budget",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "1"
      }
    },
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "cozy",
              "evidence": {
                "kind": "review_text",
                "pattern": "cozy"
              }
            },
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "coffee_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee"
              }
            },
            {
              "aspect": "espresso_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "espresso"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R59: Trendy Dog Walk
**Gold**: [17] United By Blue

**Text**: Looking for a cafe that's mid-priced and dog-friendly and trendy. Ideally known for romantic and coffee, or alternatively known for latte and tea

**Shorthand**: `AND(price_mid, dogs_yes, ambience_trendy, OR(AND(romantic_reviews, coffee_reviews), AND(latte_reviews, tea_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "price_mid",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "2"
      }
    },
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "ambience_trendy",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'trendy': True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "op": "AND",
          "args": [
            {
              "aspect": "romantic_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "romantic|date"
              }
            },
            {
              "aspect": "coffee_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee"
              }
            }
          ]
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "latte_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "latte"
              }
            },
            {
              "aspect": "tea_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "tea"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## G07


### R60: Dine-In Coffee Break
**Gold**: [32] Saxbys

**Text**: Looking for a cafe with dine-in only (no takeout). Looking for a place known for romantic or coffee. Also interested in places known for espresso or latte

**Shorthand**: `AND(takeout_no, OR(romantic_reviews, coffee_reviews), OR(espresso_reviews, latte_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "takeout_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsTakeOut"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        },
        {
          "aspect": "coffee_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "espresso_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "espresso"
          }
        },
        {
          "aspect": "latte_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "latte"
          }
        }
      ]
    }
  ]
}
```

### R61: Premium WiFi Work
**Gold**: [25] Frieda

**Text**: Looking for a cafe with paid WiFi. Looking for a place known for quiet or romantic. Also interested in places known for coffee or latte

**Shorthand**: `AND(wifi_paid, OR(quiet_reviews, romantic_reviews), OR(coffee_reviews, latte_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "wifi_paid",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "WiFi"
        ],
        "contains": "paid"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "quiet_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "quiet"
          }
        },
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "coffee_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee"
          }
        },
        {
          "aspect": "latte_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "latte"
          }
        }
      ]
    }
  ]
}
```

### R62: Intimate Evening
**Gold**: [21] K'Far Cafe

**Text**: Looking for a cafe that's intimate. Looking for a place known for romantic or coffee. Also interested in places known for espresso or latte

**Shorthand**: `AND(ambience_intimate, OR(romantic_reviews, coffee_reviews), OR(espresso_reviews, latte_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "ambience_intimate",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'intimate': True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        },
        {
          "aspect": "coffee_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "espresso_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "espresso"
          }
        },
        {
          "aspect": "latte_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "latte"
          }
        }
      ]
    }
  ]
}
```

### R63: Cozy Dog Hangout
**Gold**: [18] Chapterhouse Café & Gallery

**Text**: Looking for a cafe that's dog-friendly and indoor-only. Looking for a place known for cozy or quiet. Also interested in places known for loud or romantic

**Shorthand**: `AND(dogs_yes, outdoor_no, OR(cozy, quiet_reviews), OR(loud_reviews, romantic_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "outdoor_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "cozy",
          "evidence": {
            "kind": "review_text",
            "pattern": "cozy"
          }
        },
        {
          "aspect": "quiet_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "quiet"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "loud_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "loud|noisy"
          }
        },
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        }
      ]
    }
  ]
}
```

### R64: Dog-Friendly Meetup
**Gold**: [19] Sabrina's Café

**Text**: Looking for a cafe that's dog-friendly and known for meeting. Looking for a place known for cozy or quiet. Also interested in places known for loud or coffee

**Shorthand**: `AND(dogs_yes, meeting_reviews, OR(cozy, quiet_reviews), OR(loud_reviews, coffee_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "meeting_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "meeting"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "cozy",
          "evidence": {
            "kind": "review_text",
            "pattern": "cozy"
          }
        },
        {
          "aspect": "quiet_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "quiet"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "loud_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "loud|noisy"
          }
        },
        {
          "aspect": "coffee_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee"
          }
        }
      ]
    }
  ]
}
```

### R65: Quiet Indoor Focus
**Gold**: [14] La Colombe Coffee

**Text**: Looking for a cafe that's adult-oriented and indoor-only. Looking for a place known for cozy or quiet. Also interested in places known for loud or romantic

**Shorthand**: `AND(kids_no, outdoor_no, OR(cozy, quiet_reviews), OR(loud_reviews, romantic_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "kids_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "False"
      }
    },
    {
      "aspect": "outdoor_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "cozy",
          "evidence": {
            "kind": "review_text",
            "pattern": "cozy"
          }
        },
        {
          "aspect": "quiet_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "quiet"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "loud_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "loud|noisy"
          }
        },
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        }
      ]
    }
  ]
}
```

### R66: BYOB Hidden Gem
**Gold**: [12] Hinge Cafe

**Text**: Looking for a cafe that's BYOB and known for music. Looking for a place known for cozy or quiet. Also interested in places known for romantic or coffee

**Shorthand**: `AND(byob, music_reviews, OR(cozy, quiet_reviews), OR(romantic_reviews, coffee_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "music_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "music"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "cozy",
          "evidence": {
            "kind": "review_text",
            "pattern": "cozy"
          }
        },
        {
          "aspect": "quiet_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "quiet"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        },
        {
          "aspect": "coffee_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee"
          }
        }
      ]
    }
  ]
}
```

### R67: Classy Book Club
**Gold**: [11] Cafe La Maude

**Text**: Looking for a cafe that's BYOB and classy. Looking for a place known for cozy or romantic. Also interested in places known for coffee or latte

**Shorthand**: `AND(byob, ambience_classy, OR(cozy, romantic_reviews), OR(coffee_reviews, latte_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "ambience_classy",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Ambience"
        ],
        "contains": "'classy': True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "cozy",
          "evidence": {
            "kind": "review_text",
            "pattern": "cozy"
          }
        },
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "coffee_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee"
          }
        },
        {
          "aspect": "latte_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "latte"
          }
        }
      ]
    }
  ]
}
```

### R68: Budget Work Session
**Gold**: [5] Function Coffee Labs

**Text**: Looking for a cafe that's budget-friendly and that's BYOB. Looking for a place known for cozy or romantic. Also interested in places known for coffee or espresso

**Shorthand**: `AND(price_budget, byob, OR(cozy, romantic_reviews), OR(coffee_reviews, espresso_reviews))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "price_budget",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsPriceRange2"
        ],
        "true": "1"
      }
    },
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "cozy",
          "evidence": {
            "kind": "review_text",
            "pattern": "cozy"
          }
        },
        {
          "aspect": "romantic_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "romantic|date"
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "coffee_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "coffee"
          }
        },
        {
          "aspect": "espresso_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "espresso"
          }
        }
      ]
    }
  ]
}
```

### R69: Dog Walk Slow Service
**Gold**: [17] United By Blue

**Text**: Looking for a cafe known for slow, dog-friendly, where helpful reviews mention 'love'. Looking for a place known for gluten or where helpful reviews mention 'love'. Also interested in places known for best or recommended by experienced reviewers for work, with outdoor seating

**Shorthand**: `AND(slow_reviews, dogs_yes, review_meta_review_helpfulness_love, OR(gluten_reviews, review_meta_review_helpfulness_love), OR(best_reviews, review_meta_reviewer_experience_work), outdoor_yes)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "slow_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "slow"
      }
    },
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "review_meta_review_helpfulness_love",
      "evidence": {
        "kind": "review_text",
        "pattern": "love",
        "weight_by": {
          "field": [
            "useful"
          ]
        }
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "gluten_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "gluten"
          }
        },
        {
          "aspect": "review_meta_review_helpfulness_love",
          "evidence": {
            "kind": "review_text",
            "pattern": "love",
            "weight_by": {
              "field": [
                "useful"
              ]
            }
          }
        }
      ]
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "best_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "best"
          }
        },
        {
          "aspect": "review_meta_reviewer_experience_work",
          "evidence": {
            "kind": "review_text",
            "pattern": "work",
            "weight_by": {
              "field": [
                "user",
                "review_count"
              ]
            }
          }
        }
      ]
    },
    {
      "aspect": "outdoor_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "True"
      }
    }
  ]
}
```

## G08


### R70: Quiet Wine Evening
**Gold**: [7] Swiss Haus Cafe & Pastry Bar

**Text**: Looking for a cafe that's quiet with beer and wine. Either known for slow, or ideally both praised by elite reviewers for work and known for best

**Shorthand**: `AND(alcohol_beer_wine, noise_quiet, OR(slow_reviews, AND(review_meta_elite_status_work, best_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "alcohol_beer_wine",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "Alcohol"
        ],
        "contains": "beer_and_wine"
      }
    },
    {
      "aspect": "noise_quiet",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "NoiseLevel"
        ],
        "contains": "quiet"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "slow_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "slow"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "review_meta_elite_status_work",
              "evidence": {
                "kind": "review_text",
                "pattern": "work",
                "weight_by": {
                  "field": [
                    "user",
                    "elite"
                  ]
                }
              }
            },
            {
              "aspect": "best_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "best"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R71: Upscale Bar Night
**Gold**: [9] Gran Caffe L'Aquila

**Text**: Looking for a cafe known for slow, good for dinner. Either known for book, or ideally both endorsed by popular reviewers for love and known for beer

**Shorthand**: `AND(slow_reviews, meal_dinner, OR(books_reviews, AND(review_meta_reviewer_popularity_love, beer_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "slow_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "slow"
      }
    },
    {
      "aspect": "meal_dinner",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForMeal"
        ],
        "contains": "'dinner': True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "books_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "book"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "review_meta_reviewer_popularity_love",
              "evidence": {
                "kind": "review_text",
                "pattern": "love",
                "weight_by": {
                  "field": [
                    "user",
                    "fans"
                  ]
                }
              }
            },
            {
              "aspect": "beer_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "beer"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R72: Game Night Elite
**Gold**: [10] Thirsty Dice

**Text**: Looking for a cafe known for quiet, open Friday late night. Either known for quiet, or ideally both praised by elite reviewers for best and known for beer

**Shorthand**: `AND(quiet_reviews, hours_friday_late_night, OR(quiet_reviews, AND(review_meta_elite_status_best, beer_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "quiet_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "quiet"
      }
    },
    {
      "aspect": "hours_friday_late_night",
      "evidence": {
        "kind": "item_meta_hours",
        "path": [
          "hours",
          "Friday"
        ],
        "true": "21:0-23:0"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "quiet_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "quiet"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "review_meta_elite_status_best",
              "evidence": {
                "kind": "review_text",
                "pattern": "best",
                "weight_by": {
                  "field": [
                    "user",
                    "elite"
                  ]
                }
              }
            },
            {
              "aspect": "beer_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "beer"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R73: BYOB Classy Brunch
**Gold**: [11] Cafe La Maude

**Text**: Looking for a cafe that's where helpful reviews mention 'recommend', that's BYOB. Either known for fast, or ideally both praised by elite reviewers for work and known for brunch, without delivery

**Shorthand**: `AND(review_meta_review_helpfulness_recommend, byob, OR(fast_reviews, AND(review_meta_elite_status_work, brunch_reviews)), no_delivery)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "review_meta_review_helpfulness_recommend",
      "evidence": {
        "kind": "review_text",
        "pattern": "recommend",
        "weight_by": {
          "field": [
            "useful"
          ]
        }
      }
    },
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "fast_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "fast|quick"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "review_meta_elite_status_work",
              "evidence": {
                "kind": "review_text",
                "pattern": "work",
                "weight_by": {
                  "field": [
                    "user",
                    "elite"
                  ]
                }
              }
            },
            {
              "aspect": "brunch_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "brunch"
              }
            }
          ]
        }
      ]
    },
    {
      "aspect": "no_delivery",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "RestaurantsDelivery"
        ],
        "not_true": "True"
      }
    }
  ]
}
```

### R74: Hidden Gem BYOB
**Gold**: [12] Hinge Cafe

**Text**: Looking for a cafe known for hidden gem, that's BYOB that either endorsed by popular reviewers for love, or ideally both known for favorite and music

**Shorthand**: `AND(hidden_gem_reviews, byob, OR(review_meta_reviewer_popularity_love, AND(favorite_reviews, music_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "hidden_gem_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "hidden gem"
      }
    },
    {
      "aspect": "byob",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "BYOB"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "review_meta_reviewer_popularity_love",
          "evidence": {
            "kind": "review_text",
            "pattern": "love",
            "weight_by": {
              "field": [
                "user",
                "fans"
              ]
            }
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "favorite_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "favorite"
              }
            },
            {
              "aspect": "music_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "music"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R75: Quiet Dog Tea Time
**Gold**: [13] Steap and Grind

**Text**: Looking for a cafe that's dog-friendly with TVs. Either known for sandwich, or ideally both known for tea and art

**Shorthand**: `AND(has_tv, dogs_yes, OR(sandwich_reviews, AND(tea_reviews, art_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "has_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "True"
      }
    },
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "sandwich_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "sandwich"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "tea_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "tea"
              }
            },
            {
              "aspect": "art_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "art"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R76: Budget Quick Coffee
**Gold**: [14] La Colombe Coffee

**Text**: Looking for a cafe known for quiet, adult-oriented. Either known for work, or ideally both where helpful reviews mention 'coffee' and praised by elite reviewers for work

**Shorthand**: `AND(quiet_reviews, kids_no, OR(work_reviews, AND(review_meta_review_helpfulness_coffee, review_meta_elite_status_work)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "quiet_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "quiet"
      }
    },
    {
      "aspect": "kids_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "GoodForKids"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "work_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "work|working|laptop"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "review_meta_review_helpfulness_coffee",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee",
                "weight_by": {
                  "field": [
                    "useful"
                  ]
                }
              }
            },
            {
              "aspect": "review_meta_elite_status_work",
              "evidence": {
                "kind": "review_text",
                "pattern": "work",
                "weight_by": {
                  "field": [
                    "user",
                    "elite"
                  ]
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R77: Quiet Bike Commute
**Gold**: [16] Elixr Coffee Roasters

**Text**: Looking for a cafe known for hidden gem with TVs. Either known for favorite, or ideally both praised by elite reviewers for coffee and known for loud

**Shorthand**: `AND(hidden_gem_reviews, has_tv, OR(favorite_reviews, AND(review_meta_elite_status_coffee, loud_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "hidden_gem_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "hidden gem"
      }
    },
    {
      "aspect": "has_tv",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "HasTV"
        ],
        "true": "True"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "favorite_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "favorite"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "review_meta_elite_status_coffee",
              "evidence": {
                "kind": "review_text",
                "pattern": "coffee",
                "weight_by": {
                  "field": [
                    "user",
                    "elite"
                  ]
                }
              }
            },
            {
              "aspect": "loud_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "loud|noisy"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R78: Dog Walk Workspace
**Gold**: [18] Chapterhouse Café & Gallery

**Text**: Looking for a cafe known for organic, indoor-only. Either known for gluten, or ideally both known for love and music

**Shorthand**: `AND(organic_reviews, outdoor_no, OR(gluten_reviews, AND(love_reviews, music_reviews)))`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "organic_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "organic"
      }
    },
    {
      "aspect": "outdoor_no",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "OutdoorSeating"
        ],
        "true": "False"
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "gluten_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "gluten"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "love_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "love"
              }
            },
            {
              "aspect": "music_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "music"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### R79: BYOB Vegan Brunch
**Gold**: [19] Sabrina's Café

**Text**: Looking for a cafe known for quiet and praised by elite reviewers for recommend. Either known for fast, or ideally both where helpful reviews mention 'love' and latte, and dog-friendly

**Shorthand**: `AND(quiet_reviews, review_meta_elite_status_recommend, OR(fast_reviews, AND(review_meta_review_helpfulness_love, latte_reviews)), dogs_yes)`

**Structure**:
```json
{
  "op": "AND",
  "args": [
    {
      "aspect": "quiet_reviews",
      "evidence": {
        "kind": "review_text",
        "pattern": "quiet"
      }
    },
    {
      "aspect": "review_meta_elite_status_recommend",
      "evidence": {
        "kind": "review_text",
        "pattern": "recommend",
        "weight_by": {
          "field": [
            "user",
            "elite"
          ]
        }
      }
    },
    {
      "op": "OR",
      "args": [
        {
          "aspect": "fast_reviews",
          "evidence": {
            "kind": "review_text",
            "pattern": "fast|quick"
          }
        },
        {
          "op": "AND",
          "args": [
            {
              "aspect": "review_meta_review_helpfulness_love",
              "evidence": {
                "kind": "review_text",
                "pattern": "love",
                "weight_by": {
                  "field": [
                    "useful"
                  ]
                }
              }
            },
            {
              "aspect": "latte_reviews",
              "evidence": {
                "kind": "review_text",
                "pattern": "latte"
              }
            }
          ]
        }
      ]
    },
    {
      "aspect": "dogs_yes",
      "evidence": {
        "kind": "item_meta",
        "path": [
          "attributes",
          "DogsAllowed"
        ],
        "true": "True"
      }
    }
  ]
}
```