module madd_i303_o202 (a, b, c, r);
input [100:0] a,b,c;
output [201:0] r;

assign r = (a * b) + c;

endmodule
