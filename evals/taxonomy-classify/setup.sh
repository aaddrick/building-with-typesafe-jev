#!/usr/bin/env bash
set -euo pipefail
python3 - <<'EOF'
import json
tops = ["Home", "Electronics", "Clothing", "Sports", "Toys", "Beauty", "Automotive", "Garden", "Office", "Pets", "Grocery", "Health"]
mids = {
 "Home": ["Kitchen","Bedding","Bath","Furniture","Lighting","Decor","Storage","Cleaning","Laundry","Appliances"],
 "Electronics": ["Phones","Laptops","Audio","Cameras","TV","Gaming","Wearables","Networking","Components","Accessories"],
 "Clothing": ["Men's Tops","Men's Bottoms","Women's Tops","Women's Bottoms","Dresses","Outerwear","Shoes","Underwear","Kids","Accessories"],
 "Sports": ["Cycling","Running","Camping","Fishing","Fitness","Team Sports","Water Sports","Winter Sports","Climbing","Golf"],
 "Toys": ["Building Sets","Dolls","Puzzles","Board Games","Outdoor Play","Arts and Crafts","Vehicles","Plush","Educational","Baby Toys"],
 "Beauty": ["Skincare","Makeup","Haircare","Fragrance","Nails","Shaving","Bath and Body","Tools","Men's Grooming","Sun Care"],
 "Automotive": ["Car Care","Tools","Tires","Interior","Exterior","Electronics","Oils and Fluids","Lighting","Motorcycle","Replacement Parts"],
 "Garden": ["Plants","Seeds","Tools","Watering","Planters","Soil","Pest Control","Outdoor Furniture","Grills","Lawn Mowers"],
 "Office": ["Paper","Writing","Desk Accessories","Filing","Printers","Ink","Chairs","Desks","Mailing","Presentation"],
 "Pets": ["Dog Food","Cat Food","Dog Toys","Cat Toys","Aquarium","Bird","Small Animal","Grooming","Beds","Health"],
 "Grocery": ["Snacks","Beverages","Coffee","Tea","Baking","Pantry","Breakfast","Candy","Spices","International"],
 "Health": ["Vitamins","First Aid","Pain Relief","Cold and Flu","Digestive","Sleep","Personal Care","Medical Devices","Eye Care","Oral Care"],
}
suffixes = ["Basic","Premium","Compact","Large","Kits","Sets","Refills","Parts","Organizers","Specialty"]
tree = {t: {m: [f"{m} {s}" for s in suffixes] for m in mids[t]} for t in tops}
tree["Home"]["Kitchen"] = ["Knives","Cookware","Bakeware","Utensils","Cutting Boards","Small Appliances","Food Storage","Dinnerware","Glassware","Coffee Makers"]
json.dump(tree, open("taxonomy.json", "w"), indent=1)
EOF
