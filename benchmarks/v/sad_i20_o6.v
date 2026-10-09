module top (a, b, c, d, e, r);
    parameter BITSIZE_IN  = 4; // single input bitsize
    parameter BITSIZE_OUT = BITSIZE_IN + 2;

    input  [BITSIZE_IN-1:0]  a, b, c, d, e;
    output [BITSIZE_OUT-1:0] r;
    wire   [BITSIZE_IN-1:0]  _0, _1, _2, _3;

    assign _0 = (a > b) ? (a - b) : (b - a);
    assign _1 = (a > c) ? (a - c) : (c - a);
    assign _2 = (a > d) ? (a - d) : (d - a);
    assign _3 = (a > e) ? (a - e) : (e - a);
    assign r = _0 + _1 + _2 + _3;

endmodule
