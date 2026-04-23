module madd_i8448_o5632 (a, b, c, r);
input [2815:0] a,b,c;
output [5631:0] r;

assign r = (a * b) + c;

endmodule
