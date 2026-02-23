module abs_diff_i404_o202(a,b,r);
input [201:0] a,b;
output [201:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
