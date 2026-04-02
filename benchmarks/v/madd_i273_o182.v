module madd_i273_o182 (a, b, c, r);
input [90:0] a,b,c;
output [181:0] r;

assign r = (a * b) + c;

endmodule
