import * as THREE from "three";

import {
    OrbitControls
} from
    "three/addons/controls/OrbitControls.js";


// ============================================================
// Three.js 初始化
// ============================================================

const canvas =
    document.getElementById(
        "scene"
    );


const renderer =
    new THREE.WebGLRenderer({

        canvas:
            canvas,

        antialias:
            true

    });


renderer.setPixelRatio(

    Math.min(
        window.devicePixelRatio,
        2
    )

);


renderer.shadowMap.enabled =
    true;


renderer.shadowMap.type =
    THREE.PCFSoftShadowMap;


renderer.outputColorSpace =
    THREE.SRGBColorSpace;


// ============================================================
// Scene
// ============================================================

const scene =
    new THREE.Scene();


scene.background =
    new THREE.Color(
        0x111827
    );


// ============================================================
// Camera
// ============================================================

const camera =
    new THREE.PerspectiveCamera(

        50,
        1,
        0.1,
        100

    );


camera.position.set(

    10,
    8,
    12

);


// ============================================================
// Controls
// ============================================================

const controls =
    new OrbitControls(

        camera,
        canvas

    );


controls.target.set(

    0,
    1.6,
    0

);


controls.enableDamping =
    true;


// ============================================================
// 材质
// ============================================================

const matFloor =
    new THREE.MeshStandardMaterial({

        color:
            0x6b7280,

        roughness:
            0.85

    });


const matWall =
    new THREE.MeshStandardMaterial({

        color:
            0xe5e7eb,

        roughness:
            0.9

    });


const matTable =
    new THREE.MeshStandardMaterial({

        color:
            0x7c4a2d,

        roughness:
            0.75

    });


const matChair =
    new THREE.MeshStandardMaterial({

        color:
            0x1f2937,

        roughness:
            0.85

    });


const matDoor =
    new THREE.MeshStandardMaterial({

        color:
            0x8b5e3c,

        roughness:
            0.8

    });


const matAC =
    new THREE.MeshStandardMaterial({

        color:
            0xf8fafc,

        roughness:
            0.5

    });


const matScreen =
    new THREE.MeshStandardMaterial({

        color:
            0x111827,

        roughness:
            0.4

    });


// ============================================================
// 创建方块
// ============================================================

function box(
    name,
    size,
    pos,
    material
) {

    const mesh =
        new THREE.Mesh(

            new THREE.BoxGeometry(

                size.x,
                size.y,
                size.z

            ),

            material

        );


    mesh.name =
        name;


    mesh.position.copy(
        pos
    );


    mesh.castShadow =
        true;


    mesh.receiveShadow =
        true;


    scene.add(
        mesh
    );


    return mesh;

}


// ============================================================
// 地板
// ============================================================

box(

    "Floor",

    new THREE.Vector3(
        12,
        0.2,
        8
    ),

    new THREE.Vector3(
        0,
        -0.1,
        0
    ),

    matFloor

);


// ============================================================
// 墙
// ============================================================

box(

    "BackWall",

    new THREE.Vector3(
        12,
        4,
        0.2
    ),

    new THREE.Vector3(
        0,
        2,
        -4
    ),

    matWall

);


box(

    "LeftWall",

    new THREE.Vector3(
        0.2,
        4,
        8
    ),

    new THREE.Vector3(
        -6,
        2,
        0
    ),

    matWall

);


box(

    "RightWall",

    new THREE.Vector3(
        0.2,
        4,
        8
    ),

    new THREE.Vector3(
        6,
        2,
        0
    ),

    matWall

);


// ============================================================
// 前墙
// ============================================================

box(

    "FrontWallLeft",

    new THREE.Vector3(
        4.7,
        4,
        0.2
    ),

    new THREE.Vector3(
        -3.65,
        2,
        4
    ),

    matWall

);


box(

    "FrontWallRight",

    new THREE.Vector3(
        4.7,
        4,
        0.2
    ),

    new THREE.Vector3(
        3.65,
        2,
        4
    ),

    matWall

);


box(

    "FrontWallTop",

    new THREE.Vector3(
        2.6,
        1.0,
        0.2
    ),

    new THREE.Vector3(
        0,
        3.5,
        4
    ),

    matWall

);


// ============================================================
// 门
// ============================================================

const doorPivot =
    new THREE.Group();


doorPivot.name =
    "DoorPivot";


doorPivot.position.set(

    -1.2,
    0,
    3.88

);


scene.add(
    doorPivot
);


const door =
    new THREE.Mesh(

        new THREE.BoxGeometry(

            2.4,
            3.0,
            0.12

        ),

        matDoor

    );


door.name =
    "Door";


door.position.set(

    1.2,
    1.5,
    0

);


door.castShadow =
    true;


door.receiveShadow =
    true;


doorPivot.add(
    door
);


// ============================================================
// 会议桌
// ============================================================

box(

    "TableTop",

    new THREE.Vector3(
        5.2,
        0.22,
        2.0
    ),

    new THREE.Vector3(
        0,
        1.25,
        0
    ),

    matTable

);


for (
    const [x, z]
    of [
        [-2.2, -0.75],
        [2.2, -0.75],
        [-2.2, 0.75],
        [2.2, 0.75]
    ]
) {

    box(

        "TableLeg",

        new THREE.Vector3(
            0.18,
            1.25,
            0.18
        ),

        new THREE.Vector3(
            x,
            0.62,
            z
        ),

        matTable

    );

}


// ============================================================
// 椅子
// ============================================================

const chairPositions = [

    [-2.2, -1.7],
    [0, -1.7],
    [2.2, -1.7],

    [-2.2, 1.7],
    [0, 1.7],
    [2.2, 1.7]

];


chairPositions.forEach(

    ([x, z], i) => {

        box(

            `ChairSeat_${i}`,

            new THREE.Vector3(
                0.75,
                0.16,
                0.75
            ),

            new THREE.Vector3(
                x,
                0.7,
                z
            ),

            matChair

        );


        box(

            `ChairBack_${i}`,

            new THREE.Vector3(
                0.75,
                1.0,
                0.14
            ),

            new THREE.Vector3(

                x,
                1.18,

                z +
                (
                    z < 0
                        ? -0.32
                        : 0.32
                )

            ),

            matChair

        );

    }

);


// ============================================================
// 屏幕
// ============================================================

box(

    "Screen",

    new THREE.Vector3(
        4.4,
        2.4,
        0.12
    ),

    new THREE.Vector3(
        0,
        2.3,
        -3.86
    ),

    matScreen

);


// ============================================================
// 空调
// ============================================================

box(

    "AirConditioner",

    new THREE.Vector3(
        2.2,
        0.7,
        0.55
    ),

    new THREE.Vector3(
        4.55,
        3.1,
        -3.55
    ),

    matAC

);


const acIndicatorMat =
    new THREE.MeshStandardMaterial({

        color:
            0x334155,

        emissive:
            0x000000,

        emissiveIntensity:
            0

    });


const acIndicator =
    new THREE.Mesh(

        new THREE.SphereGeometry(
            0.08,
            20,
            20
        ),

        acIndicatorMat

    );


acIndicator.position.set(

    5.25,
    3.1,
    -3.25

);


scene.add(
    acIndicator
);


// ============================================================
// 环境光
// ============================================================

const ambient =
    new THREE.AmbientLight(

        0xffffff,
        0.45

    );


scene.add(
    ambient
);


// ============================================================
// 方向光
// ============================================================

const sun =
    new THREE.DirectionalLight(

        0xffffff,
        1.1

    );


sun.position.set(

    5,
    10,
    7

);


sun.castShadow =
    true;


scene.add(
    sun
);


// ============================================================
// 会议室灯光
// ============================================================

const roomLight =
    new THREE.PointLight(

        0xfff4d6,
        0,
        18,
        2

    );


roomLight.position.set(

    0,
    3.5,
    0

);


roomLight.castShadow =
    true;


scene.add(
    roomLight
);


const ceilingLampMat =
    new THREE.MeshStandardMaterial({

        color:
            0xd1d5db,

        emissive:
            0x000000,

        emissiveIntensity:
            0

    });


const lamp1 =
    new THREE.Mesh(

        new THREE.BoxGeometry(

            2.3,
            0.08,
            0.7

        ),

        ceilingLampMat

    );


lamp1.position.set(

    -2.2,
    3.75,
    0

);


scene.add(
    lamp1
);


const lamp2 =
    lamp1.clone();


lamp2.position.x =
    2.2;


scene.add(
    lamp2
);


// ============================================================
// 状态对象
// ============================================================

const state = {

    face_status:
        "unknown",

    person_id:
        null,

    door_status:
        "closed",

    light_status:
        "off",

    air_conditioner_status:
        "off"

};


let targetDoorAngle =
    0;


// ============================================================
// 手动重置状态
// ============================================================

let manualReset =
    false;


let externalSignatureAtReset =
    null;


// ============================================================
// UI
// ============================================================

const ui = {

    person:
        document.getElementById(
            "personStatus"
        ),

    door:
        document.getElementById(
            "doorStatus"
        ),

    light:
        document.getElementById(
            "lightStatus"
        ),

    ac:
        document.getElementById(
            "acStatus"
        )

};


function setValue(
    node,
    text,
    className
) {

    node.textContent =
        text;


    node.className =
        `value ${className}`;

}


// ============================================================
// 刷新会议室状态
// ============================================================

function renderState() {

    setValue(

        ui.person,

        state.face_status
        === "recognized"

            ? `${state.person_id} / 已授权`

            : "未识别",

        state.face_status
        === "recognized"

            ? "ok"

            : "warn"

    );


    setValue(

        ui.door,

        state.door_status
        === "open"

            ? "打开"

            : "关闭",

        state.door_status
        === "open"

            ? "ok"

            : "off"

    );


    setValue(

        ui.light,

        state.light_status
        === "on"

            ? "打开"

            : "关闭",

        state.light_status
        === "on"

            ? "ok"

            : "off"

    );


    setValue(

        ui.ac,

        state.air_conditioner_status
        === "on"

            ? "运行"

            : "关闭",

        state.air_conditioner_status
        === "on"

            ? "ok"

            : "off"

    );


    // 灯光

    roomLight.intensity =

        state.light_status
        === "on"

            ? 5.5

            : 0;


    ceilingLampMat.emissive.setHex(

        state.light_status
        === "on"

            ? 0xffd978

            : 0x000000

    );


    ceilingLampMat.emissiveIntensity =

        state.light_status
        === "on"

            ? 1.8

            : 0;


    // 空调状态灯

    acIndicatorMat.color.setHex(

        state.air_conditioner_status
        === "on"

            ? 0x22c55e

            : 0x334155

    );


    acIndicatorMat.emissive.setHex(

        state.air_conditioner_status
        === "on"

            ? 0x22c55e

            : 0x000000

    );


    acIndicatorMat.emissiveIntensity =

        state.air_conditioner_status
        === "on"

            ? 1.6

            : 0;

}


// ============================================================
// 点击按钮启动真实人脸识别
// ============================================================

async function startFaceRecognition() {

    const button =
        document.getElementById(
            "recognizeBtn"
        );


    try {

        manualReset =
            false;


        externalSignatureAtReset =
            null;


        button.disabled =
            true;


        button.textContent =
            "识别启动中...";


        const response =
            await fetch(

                "/api/recognition/start",

                {
                    method:
                        "POST"
                }

            );


        const result =
            await response.json();


        if (
            !response.ok
        ) {

            throw new Error(

                result.message
                ||
                "启动失败"

            );

        }


        button.textContent =
            "识别中...";


        console.log(
            "人脸识别程序已启动"
        );

    }


    catch (
        error
    ) {

        console.error(

            "启动人脸识别失败：",

            error

        );


        button.disabled =
            false;


        button.textContent =
            "开始人脸识别";


        alert(

            `启动人脸识别失败：${error.message}`

        );

    }

}


// ============================================================
// 重置
// ============================================================

function resetRoom() {

    manualReset =
        true;


    externalSignatureAtReset =
        JSON.stringify({

            face_status:
                state.face_status,

            person_id:
                state.person_id,

            door_status:
                state.door_status,

            light_status:
                state.light_status,

            air_conditioner_status:
                state.air_conditioner_status

        });


    state.face_status =
        "unknown";


    state.person_id =
        null;


    state.door_status =
        "closed";


    state.light_status =
        "off";


    state.air_conditioner_status =
        "off";


    targetDoorAngle =
        0;


    const button =
        document.getElementById(
            "recognizeBtn"
        );


    button.disabled =
        false;


    button.textContent =
        "开始人脸识别";


    renderState();

}


// ============================================================
// 读取 Python 输出的 state.json
// ============================================================

async function loadExternalState() {

    try {

        const response =
            await fetch(

                `./state.json?t=${Date.now()}`,

                {
                    cache:
                        "no-store"
                }

            );


        if (
            !response.ok
        ) {

            return;

        }


        const externalState =
            await response.json();


        const normalizedState = {

            face_status:

                externalState.face_status
                ?? "unknown",


            person_id:

                externalState.person_id
                ?? null,


            door_status:

                externalState.door_status
                ?? "closed",


            light_status:

                externalState.light_status
                ?? "off",


            air_conditioner_status:

                externalState
                    .air_conditioner_status
                ?? "off"

        };


        const externalSignature =
            JSON.stringify(
                normalizedState
            );


        // 手动重置后，
        // 如果外部还是旧状态，
        // 不重新覆盖。

        if (

            manualReset

            &&

            externalSignature
            ===
            externalSignatureAtReset

        ) {

            return;

        }


        // Python 产生了新状态，
        // 恢复自动联动。

        if (

            manualReset

            &&

            externalSignature
            !==
            externalSignatureAtReset

        ) {

            manualReset =
                false;


            externalSignatureAtReset =
                null;

        }


        state.face_status =
            normalizedState.face_status;


        state.person_id =
            normalizedState.person_id;


        state.door_status =
            normalizedState.door_status;


        state.light_status =
            normalizedState.light_status;


        state.air_conditioner_status =
            normalizedState
                .air_conditioner_status;


        // 门动画

        if (

            state.door_status
            ===
            "open"

        ) {

            targetDoorAngle =
                -Math.PI / 2;

        }

        else {

            targetDoorAngle =
                0;

        }


        renderState();


        // ====================================================
        // 识别成功以后恢复按钮
        // ====================================================

        if (

            state.face_status
            ===
            "recognized"

        ) {

            const button =
                document.getElementById(
                    "recognizeBtn"
                );


            button.disabled =
                false;


            button.textContent =
                "重新人脸识别";

        }

    }


    catch (
        error
    ) {

        console.error(

            "读取外部会议室状态失败：",

            error

        );

    }

}


// ============================================================
// 每 500ms 检查状态
// ============================================================

setInterval(

    loadExternalState,

    500

);


loadExternalState();


// ============================================================
// 按钮绑定
// ============================================================

document
    .getElementById(
        "recognizeBtn"
    )
    .addEventListener(

        "click",

        startFaceRecognition

    );


document
    .getElementById(
        "resetBtn"
    )
    .addEventListener(

        "click",

        resetRoom

    );


// ============================================================
// 页面尺寸
// ============================================================

function resize() {

    const width =
        window.innerWidth;


    const height =
        window.innerHeight;


    renderer.setSize(

        width,
        height,
        false

    );


    camera.aspect =
        width / height;


    camera.updateProjectionMatrix();

}


window.addEventListener(

    "resize",

    resize

);


resize();


// ============================================================
// 动画循环
// ============================================================

const clock =
    new THREE.Clock();


function animate() {

    requestAnimationFrame(
        animate
    );


    const dt =
        clock.getDelta();


    const speed =
        Math.min(
            1,
            dt * 5
        );


    doorPivot.rotation.y +=

        (
            targetDoorAngle
            -
            doorPivot.rotation.y
        )

        * speed;


    controls.update();


    renderer.render(

        scene,
        camera

    );

}


renderState();

animate();