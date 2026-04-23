module madd_i3_o2 (a, b, c, r);
input [0:0] a,b,c;
output [1:0] r;

assign r = (a * b) + c;

endmodule
