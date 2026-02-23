module madd_i297_o198 (a, b, c, r);
input [98:0] a,b,c;
output [197:0] r;

assign r = (a * b) + c;

endmodule
