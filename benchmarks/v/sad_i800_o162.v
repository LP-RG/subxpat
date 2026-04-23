module sad_i800_o162 (x0,x1,x2,x3,x4,r);
input [159:0] x0,x1,x2,x3,x4;
output [161:0] r;
wire [159:0] s1,s2,s3,s4;

assign s1 = (x0>x1) ? (x0-x1) : (x1-x0);
assign s2 = (x0>x2) ? (x0-x2) : (x2-x0);
assign s3 = (x0>x3) ? (x0-x3) : (x3-x0);
assign s4 = (x0>x4) ? (x0-x4) : (x4-x0);
assign r = s1 + s2 + s3 + s4;

endmodule
