module madd_i357_o238 (a, b, c, r);
input [118:0] a,b,c;
output [237:0] r;

assign r = (a * b) + c;

endmodule
