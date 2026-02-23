module madd_i129_o86 (a, b, c, r);
input [42:0] a,b,c;
output [85:0] r;

assign r = (a * b) + c;

endmodule
