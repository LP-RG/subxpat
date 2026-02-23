module madd_i384_o256 (a, b, c, r);
input [127:0] a,b,c;
output [255:0] r;

assign r = (a * b) + c;

endmodule
