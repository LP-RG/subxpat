module madd_i3840_o2560 (a, b, c, r);
input [1279:0] a,b,c;
output [2559:0] r;

assign r = (a * b) + c;

endmodule
