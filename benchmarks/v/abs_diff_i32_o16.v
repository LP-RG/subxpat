module top (a, b, r);
    parameter BITSIZE_IN  = 16; // single input bitsize
    parameter BITSIZE_OUT = BITSIZE_IN;

    input  [BITSIZE_IN-1:0]  a, b;
    output [BITSIZE_OUT-1:0] r;

    assign r = (a > b) ? (a - b) : (b - a);

endmodule
