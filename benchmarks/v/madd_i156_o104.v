module madd_i156_o104 (a, b, c, r);
input [51:0] a,b,c;
output [103:0] r;

assign r = (a * b) + c;

endmodule
