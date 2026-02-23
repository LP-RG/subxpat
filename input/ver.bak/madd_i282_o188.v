module madd_i282_o188 (a, b, c, r);
input [93:0] a,b,c;
output [187:0] r;

assign r = (a * b) + c;

endmodule
