module top (a, b, c, r);
    parameter BITSIZE_IN  = 5; // single input bitsize
    parameter BITSIZE_OUT = BITSIZE_IN * 2;

    input  [BITSIZE_IN-1:0]  a, b, c;
    output [BITSIZE_OUT-1:0] r;

    assign r = (a * b) + c;

endmodule
