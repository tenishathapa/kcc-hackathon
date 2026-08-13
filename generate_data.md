I will have multiple images of same locations, also many locations, generate me landmark_data.json in this format:
{
  "boudhanath_stupa": {
    "name": "Boudhanath Stupa",
    "description": "One of the largest spherical stupas in Nepal, a UNESCO World Heritage site and major Buddhist pilgrimage site.",
    "lat": 27.7215,
    "lon": 85.3620,
    folderPath:"pashupatinath"
    "images": [
      "angle_1.jpg",
      "angle_2.jpg",
      "angle_3_night.jpg",
      "angle_4_closeup.jpg"
    ]
  },
  "pashupatinath_temple": {
    "name": "Pashupatinath Temple",
    "description": "A sacred Hindu temple complex dedicated to Lord Shiva, situated on the banks of the Bagmati River.",
    "lat": 27.7106,
    "lon": 85.3487,
    "images": [
      "front.jpg",
      "side.jpg",
      "entrance.jpg"
    ]
  },
  "swayambhunath": {
    "name": "Swayambhunath (Monkey Temple)",
    "description": "An ancient religious complex atop a hill in the Kathmandu Valley, known for its iconic stupa and views of the city.",
    "lat": 27.7149,
    "lon": 85.2903,
    "images": [
      "stairs_view.jpg",
      "stupa_close.jpg"
    ]
  }
}
Scan for images in respective folder and update images array respectively. I will be uploading more dataset by time, the landmark_data.json will keep updating.