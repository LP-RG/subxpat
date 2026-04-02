module madd_i153_o102 (a, b, c, r);
input [50:0] a,b,c;
output [101:0] r;

assign r = (a * b) + c;

endmodule
