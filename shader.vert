#version 330
in vec2 in_vert;
in vec2 in_uv;
uniform vec2 in_w_ratio;
uniform vec2 in_i_ratio;
out vec2 v_uv;
void main() {
    float w_ratio = (in_w_ratio.x / in_w_ratio.y);
    float i_ratio = (in_i_ratio.x / in_i_ratio.y);

    float multip;
    if (w_ratio > i_ratio) {
        multip = i_ratio ;
    }
    else {
        multip = w_ratio;
    }

    gl_Position = vec4(
        in_vert.x / w_ratio * multip, 
        in_vert.y / i_ratio * multip,
        0.0, 1.0
    );
    v_uv = in_uv;
}
