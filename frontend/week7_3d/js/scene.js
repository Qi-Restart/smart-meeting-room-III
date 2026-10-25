import * as THREE from "three";

import {
  OrbitControls
} from "three/addons/controls/OrbitControls.js";

import {
  GLTFLoader
} from "three/addons/loaders/GLTFLoader.js";


// ============================================================
// 1. Basic DOM
// ============================================================

const canvas =
  document.getElementById("scene");

const container =
  document.getElementById("scene-container");

const loading =
  document.getElementById("loading");

const message =
  document.getElementById("message");


// ============================================================
// 2. Three.js scene
// ============================================================

const scene =
  new THREE.Scene();

scene.background =
  new THREE.Color(0xd8ddd9);


// ============================================================
// 3. Camera
// ============================================================

const camera =
  new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight,
    0.1,
    100
  );

camera.position.set(
  10,
  10,
  8
);


// ============================================================
// 4. Renderer
// ============================================================

const renderer =
  new THREE.WebGLRenderer({
    canvas,
    antialias: true
  });

renderer.setPixelRatio(
  Math.min(
    window.devicePixelRatio,
    2
  )
);

renderer.setSize(
  container.clientWidth,
  container.clientHeight
);

renderer.shadowMap.enabled = true;

renderer.shadowMap.type =
  THREE.PCFSoftShadowMap;

renderer.outputColorSpace =
  THREE.SRGBColorSpace;

renderer.toneMapping =
  THREE.ACESFilmicToneMapping;

renderer.toneMappingExposure =
  1.15;


// ============================================================
// 5. OrbitControls
// ============================================================

const controls =
  new OrbitControls(
    camera,
    renderer.domElement
  );

controls.target.set(
  0,
  1,
  0
);

controls.enableDamping = true;

controls.dampingFactor = 0.07;

controls.minDistance = 2;

controls.maxDistance = 25;

controls.maxPolarAngle =
  Math.PI / 2.05;

controls.update();


// ============================================================
// 6. Hemisphere light
// ============================================================

const hemisphereLight =
  new THREE.HemisphereLight(
    0xffffff,
    0x606b65,
    1.8
  );

scene.add(
  hemisphereLight
);


// ============================================================
// 7. Main directional light
// ============================================================

const sun =
  new THREE.DirectionalLight(
    0xfff1d5,
    2.0
  );

sun.position.set(
  6,
  10,
  6
);

sun.castShadow = true;

sun.shadow.mapSize.set(
  2048,
  2048
);

sun.shadow.camera.left = -10;
sun.shadow.camera.right = 10;
sun.shadow.camera.top = 10;
sun.shadow.camera.bottom = -10;

scene.add(
  sun
);


// ============================================================
// 8. Ground
// ============================================================

const ground =
  new THREE.Mesh(
    new THREE.PlaneGeometry(
      40,
      40
    ),

    new THREE.MeshStandardMaterial({
      color: 0xd8ddd9,
      roughness: 1
    })
  );

ground.rotation.x =
  -Math.PI / 2;

ground.position.y =
  -0.12;

ground.receiveShadow = true;

scene.add(
  ground
);


// ============================================================
// 9. GLB model variables
// ============================================================

let meetingRoom = null;

let doorPivot = null;

let light01 = null;
let light02 = null;

let airConditioner = null;


// Door animation state

let doorClosedAngle = 0;

let doorTargetAngle = 0;


// ============================================================
// 10. Load Blender GLB model
// ============================================================

const loader =
  new GLTFLoader();


loader.load(

  "./models/meeting_room.glb",


  // Load success
  (gltf) => {

    meetingRoom =
      gltf.scene;


    scene.add(
      meetingRoom
    );


    // Enable shadows
    meetingRoom.traverse(
      (object) => {

        if (object.isMesh) {

          object.castShadow = true;
          object.receiveShadow = true;

        }

      }
    );


    // Find interactive objects
    doorPivot =
      meetingRoom.getObjectByName(
        "DoorPivot"
      );


    light01 =
      meetingRoom.getObjectByName(
        "Light_01"
      );


    light02 =
      meetingRoom.getObjectByName(
        "Light_02"
      );


    airConditioner =
      meetingRoom.getObjectByName(
        "AirConditioner"
      );


    // Save closed door angle
    if (doorPivot) {

      doorClosedAngle =
        doorPivot.rotation.y;

      doorTargetAngle =
        doorClosedAngle;

      console.log(
        "DoorPivot found:",
        doorPivot
      );

    }
    else {

      console.warn(
        "DoorPivot not found"
      );

    }


    console.log(
      "Light_01:",
      light01
    );

    console.log(
      "Light_02:",
      light02
    );

    console.log(
      "AirConditioner:",
      airConditioner
    );


    loading.style.display =
      "none";


    message.textContent =
      "会议室模型加载成功";


    focusModel();

  },


  // Loading progress
  (xhr) => {

    if (
      xhr.total
      &&
      xhr.total > 0
    ) {

      const percent =
        Math.round(
          xhr.loaded
          / xhr.total
          * 100
        );


      loading.textContent =
        `正在加载会议室模型 ${percent}%`;

    }

  },


  // Load failed
  (error) => {

    console.error(
      "GLB load failed:",
      error
    );


    loading.textContent =
      "会议室模型加载失败，请检查服务器和文件路径";

  }

);


// ============================================================
// 11. Focus model
// ============================================================

function focusModel() {

  if (!meetingRoom) {

    return;

  }


  const box =
    new THREE.Box3()
      .setFromObject(
        meetingRoom
      );


  const center =
    box.getCenter(
      new THREE.Vector3()
    );


  controls.target.copy(
    center
  );


  camera.position.set(
    center.x + 10,
    center.y + 8,
    center.z + 10
  );


  controls.update();

}


// ============================================================
// 12. Door control
// ============================================================

function openDoor() {

  if (!doorPivot) {

    message.textContent =
      "没有找到 DoorPivot";

    return;

  }


  doorTargetAngle =
    doorClosedAngle
    - Math.PI / 2;


  document.getElementById(
    "doorStatus"
  ).textContent =
    "打开";


  message.textContent =
    "测试：会议室门打开";

}


function closeDoor() {

  if (!doorPivot) {

    message.textContent =
      "没有找到 DoorPivot";

    return;

  }


  doorTargetAngle =
    doorClosedAngle;


  document.getElementById(
    "doorStatus"
  ).textContent =
    "关闭";


  message.textContent =
    "测试：会议室门关闭";

}


// ============================================================
// 13. Door buttons
// ============================================================

document
  .getElementById(
    "openDoorBtn"
  )
  .addEventListener(
    "click",
    openDoor
  );


document
  .getElementById(
    "closeDoorBtn"
  )
  .addEventListener(
    "click",
    closeDoor
  );


// ============================================================
// 14. Overview camera
// ============================================================

document
  .getElementById(
    "overviewBtn"
  )
  .addEventListener(
    "click",
    () => {

      camera.position.set(
        10,
        9,
        10
      );

      controls.target.set(
        0,
        1,
        0
      );

      controls.update();

    }
  );


// ============================================================
// 15. Top camera
// ============================================================

document
  .getElementById(
    "topBtn"
  )
  .addEventListener(
    "click",
    () => {

      camera.position.set(
        0,
        15,
        0.01
      );

      controls.target.set(
        0,
        0,
        0
      );

      controls.update();

    }
  );


// ============================================================
// 16. Inside camera
// ============================================================

document
  .getElementById(
    "insideBtn"
  )
  .addEventListener(
    "click",
    () => {

      camera.position.set(
        3.2,
        2.0,
        3.0
      );

      controls.target.set(
        0,
        1.1,
        0
      );

      controls.update();

    }
  );


// ============================================================
// 17. Animation loop
// ============================================================

const clock =
  new THREE.Clock();


function animate() {

  requestAnimationFrame(
    animate
  );


  const delta =
    Math.min(
      clock.getDelta(),
      0.05
    );


  // Smooth door animation
  if (doorPivot) {

    const speed =
      1
      - Math.exp(
        -delta * 5
      );


    doorPivot.rotation.y +=
      (
        doorTargetAngle
        - doorPivot.rotation.y
      )
      * speed;

  }


  controls.update();


  renderer.render(
    scene,
    camera
  );

}


animate();


// ============================================================
// 18. Window resize
// ============================================================

function resize() {

  const width =
    container.clientWidth;

  const height =
    container.clientHeight;


  camera.aspect =
    width / height;


  camera.updateProjectionMatrix();


  renderer.setSize(
    width,
    height,
    false
  );

}


window.addEventListener(
  "resize",
  resize
);


// ============================================================
// 19. Raspberry Pi sensor APIs
//
// CMCC Wi-Fi:
// 192.168.1.228
//
// Huawei phone hotspot:
// 192.168.43.188
//
// The frontend automatically tries both addresses.
// ============================================================

const STATE_APIS = [

  "http://192.168.1.228:8081/api/rooms/R01/state",

  "http://192.168.43.188:8081/api/rooms/R01/state"

];


// Poll every 500 ms
const POLL_INTERVAL =
  500;


// Remember the last working API
let activeApiIndex = 0;


// ============================================================
// 20. Apply Raspberry Pi state
// ============================================================

function applyRoomState(state) {

  // --------------------------------------------------------
  // Temperature
  // --------------------------------------------------------

  const temperature =
    document.getElementById(
      "temperature"
    );


  if (
    typeof state.temperature
    === "number"
  ) {

    temperature.textContent =
      `${state.temperature.toFixed(1)} ℃`;

  }
  else {

    temperature.textContent =
      "-- ℃";

  }


  // --------------------------------------------------------
  // Humidity
  // --------------------------------------------------------

  const humidity =
    document.getElementById(
      "humidity"
    );


  if (
    typeof state.humidity
    === "number"
  ) {

    humidity.textContent =
      `${state.humidity.toFixed(1)} %`;

  }
  else {

    humidity.textContent =
      "-- %";

  }


  // --------------------------------------------------------
  // Light intensity
  // --------------------------------------------------------

  const lightIntensity =
    document.getElementById(
      "lightIntensity"
    );


  if (
    typeof state.light_intensity
    === "number"
  ) {

    lightIntensity.textContent =
      `${state.light_intensity.toFixed(1)} %`;

  }
  else {

    lightIntensity.textContent =
      "-- %";

  }


  // --------------------------------------------------------
  // Door state
  // --------------------------------------------------------

  if (
    state.door_status
    === "open"
  ) {

    doorTargetAngle =
      doorClosedAngle
      - Math.PI / 2;


    document.getElementById(
      "doorStatus"
    ).textContent =
      "打开";

  }
  else {

    doorTargetAngle =
      doorClosedAngle;


    document.getElementById(
      "doorStatus"
    ).textContent =
      "关闭";

  }


  // --------------------------------------------------------
  // Air conditioner state
  // --------------------------------------------------------

  const acStatus =
    document.getElementById(
      "acStatus"
    );


  if (
    state.air_conditioner_status
    === "on"
  ) {

    acStatus.textContent =
      "开启";

  }
  else {

    acStatus.textContent =
      "关闭";

  }


  // --------------------------------------------------------
  // Light sensor state
  // --------------------------------------------------------

  const lightStatus =
    document.getElementById(
      "lightStatus"
    );


  if (
    typeof state.light_intensity
    === "number"
  ) {

    lightStatus.textContent =
      "自动调节";

  }
  else {

    lightStatus.textContent =
      "数据异常";

  }


  // --------------------------------------------------------
  // Data connection state
  // --------------------------------------------------------

  document.getElementById(
    "dataStatus"
  ).textContent =
    "正常";

}


// ============================================================
// 21. Fetch Raspberry Pi state
//
// Try the last working address first.
// If it fails, automatically try the other address.
// ============================================================

async function fetchRoomState() {

  for (
    let i = 0;
    i < STATE_APIS.length;
    i++
  ) {

    const apiIndex =
      (
        activeApiIndex
        + i
      )
      % STATE_APIS.length;


    const api =
      STATE_APIS[
        apiIndex
      ];


    try {

      const response =
        await fetch(
          `${api}?t=${Date.now()}`,
          {
            cache: "no-store"
          }
        );


      if (!response.ok) {

        throw new Error(
          `HTTP ${response.status}`
        );

      }


      const state =
        await response.json();


      // Remember this working address
      activeApiIndex =
        apiIndex;


      applyRoomState(
        state
      );


      return;

    }
    catch (error) {

      console.warn(
        `Sensor API unavailable: ${api}`,
        error
      );

    }

  }


  // ========================================================
  // Both Raspberry Pi addresses failed
  // ========================================================

  document.getElementById(
    "dataStatus"
  ).textContent =
    "连接异常";


  document.getElementById(
    "temperature"
  ).textContent =
    "-- ℃";


  document.getElementById(
    "humidity"
  ).textContent =
    "-- %";


  document.getElementById(
    "lightIntensity"
  ).textContent =
    "-- %";


  document.getElementById(
    "lightStatus"
  ).textContent =
    "数据不可用";

}


// ============================================================
// 22. Start polling
// ============================================================

fetchRoomState();


setInterval(
  fetchRoomState,
  POLL_INTERVAL
);